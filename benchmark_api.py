#!/usr/bin/env python3
"""
Benchmark API Endpoint
======================

Flask API for triggering and retrieving benchmark results via HTTP
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os
import glob
import json
from datetime import datetime
from benchmark_queries import BenchmarkSuite
from query_analyzer import QueryAnalyzer

app = Flask(__name__)
CORS(app)

RESULTS_DIR = "./benchmark_results"
os.makedirs(RESULTS_DIR, exist_ok=True)


@app.route("/api/benchmark/run", methods=["POST"])
def run_benchmark():
    """
    Run complete benchmark suite
    
    Returns:
        JSON with benchmark summary and link to full results
    """
    try:
        suite = BenchmarkSuite()
        
        # Run benchmarks
        results = suite.run_all()
        
        # Save results
        json_file = suite.save_results(results, 
                                       f"{RESULTS_DIR}/benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        html_file = suite.save_report(results,
                                      f"{RESULTS_DIR}/benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        suite.close()
        
        # Identify slow queries
        slow_queries = [
            {
                "name": name,
                "avg_time_ms": data['avg_time_ms'],
                "category": data['category']
            }
            for name, data in results['results'].items()
            if 'avg_time_ms' in data and data['avg_time_ms'] > 100
        ]
        
        return jsonify({
            "ok": True,
            "timestamp": results['timestamp'],
            "summary": results['summary'],
            "slow_queries": slow_queries,
            "files": {
                "json": json_file,
                "html": html_file
            }
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/latest", methods=["GET"])
def get_latest_results():
    """
    Get the most recent benchmark results
    
    Returns:
        JSON with latest benchmark data
    """
    try:
        # Find most recent JSON file
        json_files = glob.glob(f"{RESULTS_DIR}/benchmark_results_*.json")
        
        if not json_files:
            return jsonify({
                "ok": False,
                "error": "No benchmark results found"
            }), 404
        
        latest_file = max(json_files, key=os.path.getctime)
        
        with open(latest_file, 'r') as f:
            results = json.load(f)
        
        return jsonify({
            "ok": True,
            "file": latest_file,
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/history", methods=["GET"])
def get_benchmark_history():
    """
    Get historical benchmark results
    
    Query params:
        limit: Number of recent results to return (default: 10)
    
    Returns:
        JSON array of historical benchmark summaries
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        # Get all JSON files
        json_files = glob.glob(f"{RESULTS_DIR}/benchmark_results_*.json")
        json_files.sort(key=os.path.getctime, reverse=True)
        
        history = []
        for file in json_files[:limit]:
            with open(file, 'r') as f:
                data = json.load(f)
                history.append({
                    "timestamp": data['timestamp'],
                    "file": file,
                    "summary": data['summary']
                })
        
        return jsonify({
            "ok": True,
            "count": len(history),
            "history": history
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/compare", methods=["POST"])
def compare_benchmarks():
    """
    Compare two benchmark results
    
    Body:
        {
            "baseline": "path/to/baseline.json",
            "current": "path/to/current.json"
        }
    
    Returns:
        Comparison analysis
    """
    try:
        data = request.get_json()
        baseline_file = data.get('baseline')
        current_file = data.get('current')
        
        if not baseline_file or not current_file:
            return jsonify({
                "ok": False,
                "error": "Both baseline and current files required"
            }), 400
        
        # Load both files
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        with open(current_file, 'r') as f:
            current = json.load(f)
        
        # Compare results
        comparison = {
            "baseline_timestamp": baseline['timestamp'],
            "current_timestamp": current['timestamp'],
            "improvements": [],
            "regressions": [],
            "unchanged": []
        }
        
        for query_name in baseline['results'].keys():
            if query_name not in current['results']:
                continue
            
            baseline_time = baseline['results'][query_name].get('avg_time_ms', 0)
            current_time = current['results'][query_name].get('avg_time_ms', 0)
            
            if baseline_time == 0 or current_time == 0:
                continue
            
            change_pct = ((current_time - baseline_time) / baseline_time) * 100
            
            item = {
                "query": query_name,
                "baseline_ms": baseline_time,
                "current_ms": current_time,
                "change_pct": round(change_pct, 2)
            }
            
            if change_pct < -10:  # 10% faster
                comparison['improvements'].append(item)
            elif change_pct > 10:  # 10% slower
                comparison['regressions'].append(item)
            else:
                comparison['unchanged'].append(item)
        
        # Sort by change magnitude
        comparison['improvements'].sort(key=lambda x: x['change_pct'])
        comparison['regressions'].sort(key=lambda x: x['change_pct'], reverse=True)
        
        return jsonify({
            "ok": True,
            "comparison": comparison
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/analyze", methods=["POST"])
def analyze_query():
    """
    Analyze a specific query for optimization opportunities
    
    Body:
        {
            "query": "SELECT ...",
            "params": [1, "2026-01-01"]  // optional
        }
    
    Returns:
        Query analysis with recommendations
    """
    try:
        data = request.get_json()
        query = data.get('query')
        params = tuple(data.get('params', []))
        
        if not query:
            return jsonify({
                "ok": False,
                "error": "Query is required"
            }), 400
        
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze_query(query, params if params else None)
        analyzer.close()
        
        return jsonify({
            "ok": True,
            "analysis": analysis
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/indexes", methods=["GET"])
def analyze_indexes():
    """
    Analyze all database indexes
    
    Returns:
        Index analysis and recommendations
    """
    try:
        analyzer = QueryAnalyzer()
        index_report = analyzer.analyze_all_indexes()
        analyzer.close()
        
        # Extract tables with recommendations
        needs_attention = {
            table: info
            for table, info in index_report.items()
            if info['recommendations']
        }
        
        return jsonify({
            "ok": True,
            "total_tables": len(index_report),
            "needs_attention": len(needs_attention),
            "index_report": index_report,
            "summary": needs_attention
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/report/<filename>", methods=["GET"])
def download_report(filename):
    """
    Download a specific benchmark report (HTML or JSON)
    
    Returns:
        File download
    """
    try:
        file_path = os.path.join(RESULTS_DIR, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                "ok": False,
                "error": "File not found"
            }), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/api/benchmark/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "ok": True,
        "service": "benchmark-api",
        "status": "running",
        "results_directory": RESULTS_DIR
    })


# Admin dashboard for viewing results
@app.route("/benchmark/dashboard", methods=["GET"])
def benchmark_dashboard():
    """
    Simple HTML dashboard for viewing benchmark results
    """
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .controls {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #5568d3;
        }
        #results {
            background: white;
            padding: 20px;
            border-radius: 8px;
            min-height: 200px;
        }
        .loading {
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SQL Query Benchmark Dashboard</h1>
        <p>Real-time performance monitoring</p>
    </div>
    
    <div class="controls">
        <button onclick="runBenchmark()">Run Benchmark</button>
        <button onclick="getLatestResults()">View Latest Results</button>
        <button onclick="getHistory()">View History</button>
    </div>
    
    <div id="results">
        <p class="loading">Click a button above to start</p>
    </div>
    
    <script>
        async function runBenchmark() {
            document.getElementById('results').innerHTML = '<p class="loading">Running benchmark... This may take a minute.</p>';
            
            try {
                const response = await fetch('/api/benchmark/run', { method: 'POST' });
                const data = await response.json();
                
                if (data.ok) {
                    displayResults(data);
                } else {
                    document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                }
            } catch (error) {
                document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + error + '</p>';
            }
        }
        
        async function getLatestResults() {
            document.getElementById('results').innerHTML = '<p class="loading">Loading latest results...</p>';
            
            try {
                const response = await fetch('/api/benchmark/latest');
                const data = await response.json();
                
                if (data.ok) {
                    displayResults(data.results);
                } else {
                    document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                }
            } catch (error) {
                document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + error + '</p>';
            }
        }
        
        async function getHistory() {
            document.getElementById('results').innerHTML = '<p class="loading">Loading history...</p>';
            
            try {
                const response = await fetch('/api/benchmark/history');
                const data = await response.json();
                
                if (data.ok) {
                    displayHistory(data.history);
                } else {
                    document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                }
            } catch (error) {
                document.getElementById('results').innerHTML = '<p style="color: red;">Error: ' + error + '</p>';
            }
        }
        
        function displayResults(data) {
            let html = '<h2>Benchmark Results</h2>';
            html += '<p><strong>Timestamp:</strong> ' + data.timestamp + '</p>';
            html += '<h3>Summary</h3>';
            html += '<ul>';
            html += '<li>Total Queries: ' + data.summary.total + '</li>';
            html += '<li>Successful: ' + data.summary.successful + '</li>';
            html += '<li>Average Time: ' + data.summary.avg_time_ms.toFixed(2) + 'ms</li>';
            html += '<li>Total Time: ' + data.summary.total_time_ms.toFixed(2) + 'ms</li>';
            html += '</ul>';
            
            if (data.slow_queries && data.slow_queries.length > 0) {
                html += '<h3>Slow Queries (>100ms)</h3>';
                html += '<ul>';
                data.slow_queries.forEach(q => {
                    html += '<li><strong>' + q.name + '</strong>: ' + q.avg_time_ms.toFixed(2) + 'ms (' + q.category + ')</li>';
                });
                html += '</ul>';
            }
            
            document.getElementById('results').innerHTML = html;
        }
        
        function displayHistory(history) {
            let html = '<h2>Benchmark History</h2>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<thead><tr style="background: #f0f0f0;"><th style="padding: 10px; text-align: left;">Timestamp</th><th>Total Queries</th><th>Avg Time</th></tr></thead>';
            html += '<tbody>';
            
            history.forEach(item => {
                html += '<tr style="border-bottom: 1px solid #ddd;">';
                html += '<td style="padding: 10px;">' + item.timestamp + '</td>';
                html += '<td style="padding: 10px;">' + item.summary.total + '</td>';
                html += '<td style="padding: 10px;">' + item.summary.avg_time_ms.toFixed(2) + 'ms</td>';
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            document.getElementById('results').innerHTML = html;
        }
    </script>
</body>
</html>
    """
    return html


if __name__ == "__main__":
    print("=" * 70)
    print("Benchmark API Server")
    print("=" * 70)
    print("\nEndpoints available:")
    print("  POST   /api/benchmark/run          - Run full benchmark")
    print("  GET    /api/benchmark/latest       - Get latest results")
    print("  GET    /api/benchmark/history      - Get historical results")
    print("  POST   /api/benchmark/compare      - Compare two benchmarks")
    print("  POST   /api/benchmark/analyze      - Analyze a query")
    print("  GET    /api/benchmark/indexes      - Analyze database indexes")
    print("  GET    /benchmark/dashboard        - View web dashboard")
    print("\nStarting server on http://localhost:5001")
    print("=" * 70)
    
    app.run(host="0.0.0.0", port=5001, debug=True)
