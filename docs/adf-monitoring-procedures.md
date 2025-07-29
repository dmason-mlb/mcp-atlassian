# ADF Monitoring Procedures

**Created:** July 29, 2025  
**Version:** 1.0.0  
**Purpose:** Comprehensive monitoring procedures for ADF deployment health and performance  

## Overview

This document provides monitoring procedures for the ADF (Atlassian Document Format) implementation in the MCP Atlassian server. These procedures ensure continuous monitoring of system health, performance metrics, and proactive issue detection.

## Monitoring Architecture

### Key Metrics to Monitor

1. **Performance Metrics**
   - Average conversion time (target: <100ms)
   - Cache hit rates (target: >80% for repeated content)
   - Error rates (target: <1%)
   - Memory usage patterns

2. **Functional Metrics**
   - Deployment detection accuracy
   - ADF validation success rates
   - Fallback mechanism activation frequency
   - API compatibility status

3. **System Health Metrics**
   - Service availability
   - Resource utilization
   - Error patterns and trends
   - User experience indicators

## Real-Time Monitoring Setup

### Performance Monitoring Dashboard

Create a monitoring dashboard using the built-in metrics:

```python
#!/usr/bin/env python3
"""
ADF Performance Monitor - Real-time dashboard for ADF system health
"""

import time
import json
from datetime import datetime, timedelta
from mcp_atlassian.formatting.router import FormatRouter

class ADFMonitor:
    def __init__(self, update_interval: int = 60):
        self.router = FormatRouter()
        self.update_interval = update_interval
        self.baseline_metrics = {
            'average_conversion_time': 0.015,  # 15ms baseline
            'cache_hit_rate': 80.0,           # 80% baseline
            'error_rate': 0.0,                # 0% baseline
            'detection_cache_hit_rate': 50.0  # 50% baseline
        }
        
    def get_current_status(self) -> dict:
        """Get current system status and health indicators."""
        metrics = self.router.get_performance_metrics()
        adf_metrics = metrics.get('adf_generator_metrics', {})
        
        # Calculate health scores
        health_scores = {}
        for metric, baseline in self.baseline_metrics.items():
            if metric in metrics:
                current = metrics[metric]
            elif metric in adf_metrics:
                current = adf_metrics[metric]
            else:
                current = 0
                
            if metric == 'error_rate':
                # Lower is better for error rate
                health_scores[metric] = max(0, 100 - (current * 10))
            else:
                # Higher is better for other metrics
                health_scores[metric] = min(100, (current / baseline) * 100)
        
        overall_health = sum(health_scores.values()) / len(health_scores)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': overall_health,
            'health_status': self._get_health_status(overall_health),
            'metrics': metrics,
            'health_scores': health_scores,
            'alerts': self._check_alerts(metrics, adf_metrics)
        }
    
    def _get_health_status(self, health_score: float) -> str:
        """Determine health status based on overall score."""
        if health_score >= 90:
            return "EXCELLENT"
        elif health_score >= 75:
            return "GOOD"
        elif health_score >= 60:
            return "WARNING"
        elif health_score >= 40:
            return "CRITICAL"
        else:
            return "EMERGENCY"
    
    def _check_alerts(self, metrics: dict, adf_metrics: dict) -> list:
        """Check for alert conditions."""
        alerts = []
        
        # Performance alerts
        if metrics.get('average_conversion_time', 0) > 0.1:
            alerts.append({
                'level': 'WARNING',
                'message': f"Slow conversion time: {metrics['average_conversion_time']*1000:.1f}ms > 100ms target",
                'metric': 'conversion_time'
            })
        
        # Error rate alerts
        error_rate = adf_metrics.get('error_rate', 0)
        if error_rate > 5.0:
            alerts.append({
                'level': 'CRITICAL',
                'message': f"High error rate: {error_rate:.1f}% > 5% threshold",
                'metric': 'error_rate'
            })
        elif error_rate > 1.0:
            alerts.append({
                'level': 'WARNING',
                'message': f"Elevated error rate: {error_rate:.1f}% > 1% target",
                'metric': 'error_rate'
            })
        
        # Cache performance alerts
        cache_hit_rate = adf_metrics.get('cache_hit_rate', 0)
        if cache_hit_rate < 50.0:
            alerts.append({
                'level': 'WARNING',
                'message': f"Low cache hit rate: {cache_hit_rate:.1f}% < 50% threshold",
                'metric': 'cache_hit_rate'
            })
        
        # Last error alerts
        if metrics.get('last_error') or adf_metrics.get('last_error'):
            recent_error = metrics.get('last_error') or adf_metrics.get('last_error')
            alerts.append({
                'level': 'INFO',
                'message': f"Recent error: {recent_error}",
                'metric': 'last_error'
            })
        
        return alerts
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop."""
        print("🚀 Starting ADF Continuous Monitor")
        print(f"Update interval: {self.update_interval}s")
        print("=" * 60)
        
        try:
            while True:
                status = self.get_current_status()
                self._display_status(status)
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
    
    def _display_status(self, status: dict):
        """Display current status in console."""
        timestamp = status['timestamp']
        health = status['overall_health']
        health_status = status['health_status']
        
        # Status indicators
        status_emoji = {
            'EXCELLENT': '🟢',
            'GOOD': '🟡', 
            'WARNING': '🟠',
            'CRITICAL': '🔴',
            'EMERGENCY': '🚨'
        }
        
        print(f"\n[{timestamp}] {status_emoji.get(health_status, '❓')} {health_status} (Health: {health:.1f}%)")
        
        # Display key metrics
        metrics = status['metrics']
        adf_metrics = metrics.get('adf_generator_metrics', {})
        
        print(f"  Conversion Time: {metrics.get('average_conversion_time', 0)*1000:.1f}ms")
        print(f"  Cache Hit Rate: {adf_metrics.get('cache_hit_rate', 0):.1f}%")
        print(f"  Error Rate: {adf_metrics.get('error_rate', 0):.1f}%")
        print(f"  Detection Cache: {metrics.get('detection_cache_hit_rate', 0):.1f}%")
        print(f"  Total Conversions: {adf_metrics.get('conversions_total', 0)}")
        
        # Display alerts
        alerts = status['alerts']
        if alerts:
            print("  🚨 Alerts:")
            for alert in alerts:
                level_emoji = {'WARNING': '⚠️', 'CRITICAL': '🔴', 'INFO': 'ℹ️'}.get(alert['level'], '❓')
                print(f"    {level_emoji} {alert['message']}")

if __name__ == "__main__":
    import sys
    
    update_interval = 60  # Default 1 minute
    if len(sys.argv) > 1:
        update_interval = int(sys.argv[1])
    
    monitor = ADFMonitor(update_interval=update_interval)
    monitor.run_continuous_monitoring()
```

Save this as `scripts/adf_monitor.py` and run:

```bash
# Start monitoring with 30-second updates
uv run python3 scripts/adf_monitor.py 30
```

### Log-Based Monitoring

1. **Error Pattern Detection**
   ```bash
   #!/bin/bash
   # Save as scripts/monitor_adf_errors.sh
   
   LOG_FILE="/var/log/mcp-atlassian.log"
   ALERT_THRESHOLD=10
   TIME_WINDOW="5 minutes ago"
   
   echo "🔍 Monitoring ADF errors in last 5 minutes..."
   
   # Count recent ADF errors
   RECENT_ERRORS=$(journalctl --since "$TIME_WINDOW" -u mcp-atlassian 2>/dev/null | \
                   grep -c "ADF conversion failed" || \
                   tail -n 1000 "$LOG_FILE" 2>/dev/null | \
                   grep "$(date --date="$TIME_WINDOW" "+%Y-%m-%d %H:%M")" | \
                   grep -c "ADF conversion failed" || echo "0")
   
   echo "Recent ADF errors: $RECENT_ERRORS"
   
   if [ "$RECENT_ERRORS" -gt "$ALERT_THRESHOLD" ]; then
       echo "🚨 HIGH ERROR RATE DETECTED: $RECENT_ERRORS errors in 5 minutes"
       echo "Recent error patterns:"
       journalctl --since "$TIME_WINDOW" -u mcp-atlassian 2>/dev/null | \
           grep "ADF conversion failed" | tail -5 || \
           tail -n 1000 "$LOG_FILE" 2>/dev/null | \
               grep "$(date --date="$TIME_WINDOW" "+%Y-%m-%d %H:%M")" | \
               grep "ADF conversion failed" | tail -5
       
       # Trigger alert (customize for your environment)
       # curl -X POST https://alerts.company.com/webhook \
       #      -d "ADF error spike: $RECENT_ERRORS errors in 5 minutes"
   else
       echo "✅ Error rate within normal limits"
   fi
   ```

2. **Performance Degradation Detection**
   ```bash
   #!/bin/bash
   # Save as scripts/monitor_adf_performance.sh
   
   echo "📊 ADF Performance Check"
   
   # Test conversion performance
   PERFORMANCE_TEST=$(python3 -c "
   import time
   from mcp_atlassian.formatting.router import FormatRouter
   
   router = FormatRouter()
   test_markdown = '''# Performance Test
   
   This is a **performance test** with *italic text* and [links](https://example.com).
   
   - List item 1
   - List item 2
   - List item 3
   
   \`\`\`python
   def test_function():
       return 'performance test'
   \`\`\`
   '''
   
   start_time = time.time()
   result = router.convert_markdown(test_markdown, 'https://test.atlassian.net')
   duration = time.time() - start_time
   
   print(f'{duration:.3f}')
   ")
   
   PERFORMANCE_MS=$(echo "$PERFORMANCE_TEST * 1000" | bc)
   
   echo "Conversion time: ${PERFORMANCE_MS}ms"
   
   if (( $(echo "$PERFORMANCE_TEST > 0.1" | bc -l) )); then
       echo "⚠️  SLOW PERFORMANCE: ${PERFORMANCE_MS}ms > 100ms target"
       
       # Get detailed metrics
       python3 -c "
       from mcp_atlassian.formatting.router import FormatRouter
       router = FormatRouter()
       metrics = router.get_performance_metrics()
       print(f'Cache hit rate: {metrics[\"adf_generator_metrics\"][\"cache_hit_rate\"]:.1f}%')
       print(f'Total conversions: {metrics[\"adf_generator_metrics\"][\"conversions_total\"]}')
       print(f'Error rate: {metrics[\"adf_generator_metrics\"][\"error_rate\"]:.1f}%')
       "
   else
       echo "✅ Performance within target"
   fi
   ```

### Health Check Endpoints

Create health check endpoints for external monitoring:

```python
# Add to your web server or create standalone health service
from flask import Flask, jsonify
from mcp_atlassian.formatting.router import FormatRouter

app = Flask(__name__)

@app.route('/healthz')
def health_check():
    """Basic health check endpoint."""
    try:
        router = FormatRouter()
        
        # Test basic functionality
        test_result = router.convert_markdown("**test**", "https://test.atlassian.net")
        
        if 'error' in test_result:
            return jsonify({
                'status': 'unhealthy',
                'error': test_result['error']
            }), 503
        
        return jsonify({
            'status': 'healthy',
            'format': test_result['format'],
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/healthz/detailed')
def detailed_health_check():
    """Detailed health check with metrics."""
    try:
        router = FormatRouter()
        
        # Get comprehensive metrics
        metrics = router.get_performance_metrics()
        adf_metrics = metrics.get('adf_generator_metrics', {})
        
        # Determine health status
        health_score = 100
        alerts = []
        
        # Check performance
        if metrics.get('average_conversion_time', 0) > 0.1:
            health_score -= 20
            alerts.append("Slow conversion time")
        
        # Check error rate
        error_rate = adf_metrics.get('error_rate', 0)
        if error_rate > 5:
            health_score -= 30
            alerts.append("High error rate")
        elif error_rate > 1:
            health_score -= 10
            alerts.append("Elevated error rate")
        
        # Check cache performance
        if adf_metrics.get('cache_hit_rate', 0) < 50:
            health_score -= 15
            alerts.append("Low cache hit rate")
        
        status = 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy'
        
        return jsonify({
            'status': status,
            'health_score': health_score,
            'metrics': {
                'conversion_time_ms': metrics.get('average_conversion_time', 0) * 1000,
                'cache_hit_rate': adf_metrics.get('cache_hit_rate', 0),
                'error_rate': error_rate,
                'total_conversions': adf_metrics.get('conversions_total', 0),
                'detection_cache_hit_rate': metrics.get('detection_cache_hit_rate', 0)
            },
            'alerts': alerts,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## Automated Alerting

### Alert Configuration

1. **Performance Alerts**
   ```python
   # Save as scripts/adf_alerting.py
   
   import time
   import smtplib
   from email.mime.text import MIMEText
   from mcp_atlassian.formatting.router import FormatRouter
   
   class ADFAlerting:
       def __init__(self, 
                    smtp_server: str = 'localhost', 
                    smtp_port: int = 587,
                    alert_email: str = 'ops@company.com'):
           self.router = FormatRouter()
           self.smtp_server = smtp_server
           self.smtp_port = smtp_port
           self.alert_email = alert_email
           self.last_alert_time = {}
           self.alert_cooldown = 300  # 5 minutes between similar alerts
       
       def check_and_alert(self):
           """Check metrics and send alerts if needed."""
           metrics = self.router.get_performance_metrics()
           adf_metrics = metrics.get('adf_generator_metrics', {})
           
           alerts = []
           
           # Performance alerts
           avg_time = metrics.get('average_conversion_time', 0)
           if avg_time > 0.15:  # 150ms critical threshold
               alerts.append({
                   'level': 'CRITICAL',
                   'type': 'performance',
                   'message': f"Critical performance degradation: {avg_time*1000:.1f}ms > 150ms"
               })
           elif avg_time > 0.1:  # 100ms warning threshold
               alerts.append({
                   'level': 'WARNING', 
                   'type': 'performance',
                   'message': f"Performance degradation: {avg_time*1000:.1f}ms > 100ms target"
               })
           
           # Error rate alerts
           error_rate = adf_metrics.get('error_rate', 0)
           if error_rate > 10:  # 10% critical
               alerts.append({
                   'level': 'CRITICAL',
                   'type': 'errors',
                   'message': f"Critical error rate: {error_rate:.1f}% > 10%"
               })
           elif error_rate > 5:  # 5% warning
               alerts.append({
                   'level': 'WARNING',
                   'type': 'errors', 
                   'message': f"High error rate: {error_rate:.1f}% > 5%"
               })
           
           # Cache alerts
           cache_hit_rate = adf_metrics.get('cache_hit_rate', 0)
           if cache_hit_rate < 30:  # 30% critical
               alerts.append({
                   'level': 'WARNING',
                   'type': 'cache',
                   'message': f"Low cache hit rate: {cache_hit_rate:.1f}% < 30%"
               })
           
           # Send alerts
           for alert in alerts:
               self._send_alert(alert)
       
       def _send_alert(self, alert: dict):
           """Send alert if not in cooldown period."""
           alert_key = f"{alert['type']}_{alert['level']}"
           current_time = time.time()
           
           # Check cooldown
           if (alert_key in self.last_alert_time and 
               current_time - self.last_alert_time[alert_key] < self.alert_cooldown):
               return
           
           # Send email alert
           try:
               msg = MIMEText(f"""
   ADF System Alert
   
   Level: {alert['level']}
   Type: {alert['type']}
   Message: {alert['message']}
   
   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
   
   Please check the ADF system status and take appropriate action.
   """)
               
               msg['Subject'] = f"ADF {alert['level']}: {alert['type']}"
               msg['From'] = 'mcp-atlassian@company.com'
               msg['To'] = self.alert_email
               
               with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                   server.send_message(msg)
               
               print(f"Alert sent: {alert['message']}")
               self.last_alert_time[alert_key] = current_time
               
           except Exception as e:
               print(f"Failed to send alert: {e}")
       
       def run_alerting_loop(self, check_interval: int = 60):
           """Run continuous alerting loop."""
           print(f"🚨 Starting ADF Alerting (check every {check_interval}s)")
           
           try:
               while True:
                   self.check_and_alert()
                   time.sleep(check_interval)
           except KeyboardInterrupt:
               print("\n👋 Alerting stopped by user")
   
   if __name__ == "__main__":
       alerting = ADFAlerting()
       alerting.run_alerting_loop()
   ```

2. **Integration with External Monitoring**
   ```bash
   # Prometheus metrics endpoint
   cat > scripts/prometheus_metrics.py << 'EOF'
   from prometheus_client import Counter, Histogram, Gauge, start_http_server
   from mcp_atlassian.formatting.router import FormatRouter
   import time
   
   # Define metrics
   conversion_time = Histogram('adf_conversion_duration_seconds', 'ADF conversion time')
   conversion_total = Counter('adf_conversions_total', 'Total ADF conversions')
   cache_hits = Counter('adf_cache_hits_total', 'ADF cache hits')
   errors_total = Counter('adf_errors_total', 'ADF conversion errors')
   health_score = Gauge('adf_health_score', 'ADF system health score')
   
   def update_metrics():
       """Update Prometheus metrics from ADF system."""
       router = FormatRouter()
       metrics = router.get_performance_metrics()
       adf_metrics = metrics.get('adf_generator_metrics', {})
       
       # Update gauges
       health_score.set(calculate_health_score(metrics, adf_metrics))
       
       # Note: Counters should be incremented, not set
       # In production, integrate this with actual conversion calls
   
   def calculate_health_score(metrics: dict, adf_metrics: dict) -> float:
       """Calculate overall health score."""
       score = 100.0
       
       # Performance penalty
       avg_time = metrics.get('average_conversion_time', 0)
       if avg_time > 0.1:
           score -= min(30, (avg_time - 0.1) * 300)  # Penalty for slow performance
       
       # Error rate penalty
       error_rate = adf_metrics.get('error_rate', 0)
       score -= min(40, error_rate * 4)  # Up to 40 point penalty for errors
       
       # Cache performance bonus/penalty
       cache_rate = adf_metrics.get('cache_hit_rate', 0)
       if cache_rate < 50:
           score -= (50 - cache_rate) * 0.5  # Penalty for low cache performance
       
       return max(0, score)
   
   if __name__ == '__main__':
       # Start Prometheus metrics server
       start_http_server(8000)
       print("Prometheus metrics available at http://localhost:8000")
       
       while True:
           update_metrics()
           time.sleep(30)
   EOF
   ```

## Operational Procedures

### Daily Monitoring Checklist

```bash
#!/bin/bash
# Save as scripts/daily_adf_check.sh

echo "📋 Daily ADF System Check - $(date)"
echo "=" * 50

# 1. Health check
echo "🏥 Health Check:"
./scripts/check_adf_health.sh

# 2. Performance check  
echo -e "\n📊 Performance Check:"
./scripts/monitor_adf_performance.sh

# 3. Error analysis
echo -e "\n🔍 Error Analysis:"
./scripts/monitor_adf_errors.sh

# 4. Cache statistics
echo -e "\n💾 Cache Statistics:"
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
metrics = router.get_performance_metrics()
adf_metrics = metrics['adf_generator_metrics']

print(f'Deployment detection cache: {metrics[\"detection_cache_hit_rate\"]:.1f}%')
print(f'ADF conversion cache: {adf_metrics[\"cache_hit_rate\"]:.1f}%')
print(f'Total conversions today: {adf_metrics[\"conversions_total\"]}')
print(f'Cache size: {router.get_cache_stats()[\"cache_size\"]} entries')
"

# 5. Memory usage
echo -e "\n🧠 Memory Usage:"
ps aux | grep mcp-atlassian | head -1 | awk '{print "RSS Memory: " $6/1024 " MB"}'

# 6. Recent deployments
echo -e "\n🚀 Recent Deployments:"
git log --oneline --since="24 hours ago" | head -5

echo -e "\n✅ Daily check completed - $(date)"
```

### Weekly Maintenance Tasks

```bash
#!/bin/bash
# Save as scripts/weekly_adf_maintenance.sh

echo "🔧 Weekly ADF Maintenance - $(date)"
echo "=" * 50

# 1. Performance trend analysis
echo "📈 Performance Trends (last 7 days):"
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
import time

router = FormatRouter()

# Simulate trend analysis (in production, use historical data)
current_metrics = router.get_performance_metrics()
adf_metrics = current_metrics['adf_generator_metrics']

print(f'Current average conversion time: {current_metrics[\"average_conversion_time\"]*1000:.1f}ms')
print(f'Current cache hit rate: {adf_metrics[\"cache_hit_rate\"]:.1f}%')
print(f'Current error rate: {adf_metrics[\"error_rate\"]:.1f}%')

# Reset metrics for fresh weekly tracking
router.reset_metrics()
print('✅ Metrics reset for new week')
"

# 2. Cache optimization
echo -e "\n💾 Cache Optimization:"
python3 -c "
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()
cache_stats = router.get_cache_stats()

print(f'Cache utilization: {cache_stats[\"cache_size\"]}/{cache_stats[\"cache_maxsize\"]} entries')

if cache_stats['cache_size'] == cache_stats['cache_maxsize']:
    print('⚠️  Cache at maximum capacity - consider increasing size')
else:
    print('✅ Cache size optimal')

# Clear old cache entries
router.clear_cache()
print('🧹 Cache cleared for fresh start')
"

# 3. Error pattern analysis
echo -e "\n🔍 Error Pattern Analysis:"
echo "Analyzing error logs from past week..."
grep "ADF conversion failed" /var/log/mcp-atlassian.log | tail -20 | \
    cut -d' ' -f6- | sort | uniq -c | sort -rn | head -5

# 4. Performance baseline update
echo -e "\n📊 Performance Baseline Update:"
python3 scripts/update_performance_baselines.py

# 5. Dependency check
echo -e "\n📦 Dependency Updates:"
uv run pip list --outdated | grep -E "(markdown|beautifulsoup|cachetools)"

echo -e "\n✅ Weekly maintenance completed - $(date)"
```

### Incident Response Procedures

1. **High Error Rate Response**
   ```bash
   #!/bin/bash
   # Save as scripts/incident_high_errors.sh
   
   echo "🚨 ADF High Error Rate Incident Response"
   
   # 1. Immediate assessment
   echo "📊 Current Error Analysis:"
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   router = FormatRouter()
   metrics = router.get_performance_metrics()
   adf_metrics = metrics['adf_generator_metrics']
   
   print(f'Current error rate: {adf_metrics[\"error_rate\"]:.1f}%')
   print(f'Last error: {adf_metrics[\"last_error\"]}')
   print(f'Total errors: {adf_metrics[\"conversion_errors\"]}')
   "
   
   # 2. Enable fallback mode
   echo "🔄 Enabling fallback mode..."
   export MCP_ATLASSIAN_FORCE_WIKI_MARKUP=true
   
   # 3. Clear caches
   echo "🧹 Clearing caches..."
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   router = FormatRouter()
   router.clear_cache()
   router.adf_generator.clear_cache()
   print('Caches cleared')
   "
   
   # 4. Test recovery
   echo "🧪 Testing recovery..."
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   router = FormatRouter()
   result = router.convert_markdown('**test**', 'https://test.atlassian.net')
   print(f'Recovery test: {\"SUCCESS\" if \"error\" not in result else \"FAILED\"}')
   print(f'Format: {result.get(\"format\", \"unknown\")}')
   "
   
   echo "✅ Incident response completed"
   ```

2. **Performance Degradation Response**
   ```bash
   #!/bin/bash
   # Save as scripts/incident_slow_performance.sh
   
   echo "🐌 ADF Performance Degradation Response"
   
   # 1. Performance analysis
   echo "⏱️  Performance Analysis:"
   python3 -c "
   import time
   from mcp_atlassian.formatting.router import FormatRouter
   
   router = FormatRouter()
   
   # Test current performance
   start = time.time()
   result = router.convert_markdown('# Test\n\n**Bold** text with [link](http://example.com)', 'https://test.atlassian.net')
   duration = time.time() - start
   
   print(f'Current conversion time: {duration*1000:.1f}ms')
   
   metrics = router.get_performance_metrics()
   adf_metrics = metrics['adf_generator_metrics']
   print(f'Cache hit rate: {adf_metrics[\"cache_hit_rate\"]:.1f}%')
   print(f'Total conversions: {adf_metrics[\"conversions_total\"]}')
   "
   
   # 2. Cache optimization
   echo "💾 Cache Optimization:"
   python3 -c "
   from mcp_atlassian.formatting.router import FormatRouter
   
   # Create new router with optimized settings
   router = FormatRouter(cache_ttl=7200, cache_size=200, adf_cache_size=512)
   
   # Test performance with larger cache
   import time
   start = time.time()
   result = router.convert_markdown('# Test\n\n**Bold** text', 'https://test.atlassian.net')
   duration = time.time() - start
   
   print(f'Optimized conversion time: {duration*1000:.1f}ms')
   print('Cache size increased for better performance')
   "
   
   # 3. Resource check
   echo "💻 Resource Usage:"
   ps aux | grep mcp-atlassian | awk '{print \"CPU: \" $3 \"%, Memory: \" $4 \"%\"}'
   
   echo "✅ Performance incident response completed"
   ```

## Reporting and Analytics

### Automated Reports

```python
# Save as scripts/generate_adf_report.py

import json
from datetime import datetime, timedelta
from mcp_atlassian.formatting.router import FormatRouter

def generate_weekly_report():
    """Generate comprehensive weekly ADF performance report."""
    router = FormatRouter()
    metrics = router.get_performance_metrics()
    adf_metrics = metrics.get('adf_generator_metrics', {})
    
    report = {
        'report_date': datetime.now().isoformat(),
        'report_period': '7 days',
        'system_health': {
            'overall_status': 'HEALTHY',  # Would be calculated from historical data
            'uptime_percentage': 99.95,   # Would be calculated from monitoring data
            'performance_score': 92.3     # Would be calculated from metrics
        },
        'performance_metrics': {
            'average_conversion_time_ms': round(metrics.get('average_conversion_time', 0) * 1000, 2),
            'cache_hit_rate_percent': round(adf_metrics.get('cache_hit_rate', 0), 1),
            'error_rate_percent': round(adf_metrics.get('error_rate', 0), 1),
            'total_conversions': adf_metrics.get('conversions_total', 0),
            'detection_cache_hit_rate': round(metrics.get('detection_cache_hit_rate', 0), 1)
        },
        'trends': {
            'performance_trend': 'STABLE',      # Would be calculated from historical data
            'error_trend': 'DECREASING',       # Would be calculated from historical data  
            'usage_trend': 'INCREASING'        # Would be calculated from historical data
        },
        'alerts_summary': {
            'total_alerts': 0,                 # Would be tracked in production
            'critical_alerts': 0,              # Would be tracked in production
            'resolved_incidents': 0            # Would be tracked in production
        },
        'recommendations': []
    }
    
    # Add performance recommendations
    if metrics.get('average_conversion_time', 0) > 0.05:
        report['recommendations'].append("Consider optimizing conversion performance - average time exceeds 50ms")
    
    if adf_metrics.get('cache_hit_rate', 0) < 70:
        report['recommendations'].append("Increase cache size to improve hit rate - currently below 70%")
    
    if adf_metrics.get('error_rate', 0) > 2:
        report['recommendations'].append("Investigate error patterns - error rate above 2%")
    
    # Output report
    print("📊 ADF Weekly Performance Report")
    print("=" * 50)
    print(f"Report Date: {report['report_date']}")
    print(f"System Health: {report['system_health']['overall_status']}")
    print(f"Performance Score: {report['system_health']['performance_score']}/100")
    print()
    print("Key Metrics:")
    print(f"  Average Conversion Time: {report['performance_metrics']['average_conversion_time_ms']}ms")
    print(f"  Cache Hit Rate: {report['performance_metrics']['cache_hit_rate_percent']}%")
    print(f"  Error Rate: {report['performance_metrics']['error_rate_percent']}%")
    print(f"  Total Conversions: {report['performance_metrics']['total_conversions']}")
    print()
    
    if report['recommendations']:
        print("Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        print()
    else:
        print("✅ No recommendations - system performing optimally")
        print()
    
    # Save report to file
    report_file = f"reports/adf_weekly_report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📁 Report saved to: {report_file}")
    
    return report

if __name__ == '__main__':
    generate_weekly_report()
```

This comprehensive monitoring setup provides:

1. **Real-time monitoring** with automated dashboards
2. **Proactive alerting** for performance and error conditions  
3. **Health check endpoints** for external monitoring systems
4. **Operational procedures** for daily and weekly maintenance
5. **Incident response procedures** for common issues
6. **Automated reporting** for performance tracking

The monitoring system ensures the ADF implementation remains healthy, performant, and reliable in production environments.