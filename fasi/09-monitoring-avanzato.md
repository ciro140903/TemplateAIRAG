# 📊 FASE 09: MONITORING AVANZATO

## 📋 Panoramica Fase

Implementazione del sistema di monitoring completo con Grafana, Loki, Promtail, metriche custom, alerting intelligente, e dashboard analytics per monitoraggio avanzato di tutte le componenti del sistema.

## 🎯 Obiettivi

- **Monitoring Stack Completo**: Grafana + Loki + Promtail integration
- **Custom Metrics**: Application-specific monitoring
- **Intelligent Alerting**: Proactive issue detection
- **Performance Analytics**: Real-time e historical data
- **Health Dashboards**: System status overview

## ⏱️ Timeline

- **Durata Stimata**: 5-7 giorni
- **Priorità**: ⭐⭐ ALTA
- **Dipendenze**: Fase 01 (Setup Infrastrutturale), tutte le fasi precedenti
- **Parallelo con**: Fase 10 (Testing e Deployment)

## 🛠️ Task Dettagliati

### 1. Enhanced Grafana Configuration

- [ ] **Custom Dashboards Configuration**
  ```yaml
  # monitoring/grafana/dashboards/system-overview.json
  {
    "dashboard": {
      "id": null,
      "title": "Sistema Overview",
      "tags": ["sistema", "overview"],
      "timezone": "Europe/Rome",
      "panels": [
        {
          "id": 1,
          "title": "System Health",
          "type": "stat",
          "targets": [
            {
              "expr": "up{job=\"backend\"}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "thresholds": {
                "steps": [
                  {"color": "red", "value": 0},
                  {"color": "green", "value": 1}
                ]
              }
            }
          }
        },
        {
          "id": 2,
          "title": "API Response Time",
          "type": "graph",
          "targets": [
            {
              "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
            }
          ]
        },
        {
          "id": 3,
          "title": "Active Users",
          "type": "stat",
          "targets": [
            {
              "expr": "active_users_total"
            }
          ]
        },
        {
          "id": 4,
          "title": "Chat Messages Rate",
          "type": "graph",
          "targets": [
            {
              "expr": "rate(chat_messages_total[5m])"
            }
          ]
        },
        {
          "id": 5,
          "title": "Indexing Jobs Status",
          "type": "table",
          "targets": [
            {
              "expr": "indexing_jobs_by_status"
            }
          ]
        },
        {
          "id": 6,
          "title": "Error Rate",
          "type": "graph",
          "targets": [
            {
              "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m])"
            }
          ]
        }
      ],
      "time": {
        "from": "now-1h",
        "to": "now"
      },
      "refresh": "30s"
    }
  }
  ```

- [ ] **AI/Chat Specific Dashboard**
  ```yaml
  # monitoring/grafana/dashboards/ai-chat-analytics.json
  {
    "dashboard": {
      "title": "AI & Chat Analytics",
      "panels": [
        {
          "title": "Chat Sessions Active",
          "type": "stat",
          "targets": [{"expr": "chat_sessions_active"}]
        },
        {
          "title": "AI Response Time Distribution",
          "type": "histogram",
          "targets": [{"expr": "ai_response_duration_seconds_bucket"}]
        },
        {
          "title": "RAG Query Success Rate",
          "type": "gauge",
          "targets": [{"expr": "rag_query_success_rate"}]
        },
        {
          "title": "Vector Search Performance",
          "type": "graph",
          "targets": [{"expr": "vector_search_duration_seconds"}]
        },
        {
          "title": "Token Usage by Model",
          "type": "table",
          "targets": [{"expr": "ai_tokens_used_total by (model)"}]
        },
        {
          "title": "User Satisfaction Scores",
          "type": "graph",
          "targets": [{"expr": "user_satisfaction_score"}]
        }
      ]
    }
  }
  ```

### 2. Backend Metrics Collection

- [ ] **Metrics Service**
  ```python
  # backend/app/services/metrics_service.py
  from prometheus_client import Counter, Histogram, Gauge, Info
  import time
  from functools import wraps
  from typing import Dict, Any, Optional
  import asyncio
  
  class MetricsService:
      def __init__(self):
          # HTTP Metrics
          self.http_requests_total = Counter(
              'http_requests_total',
              'Total HTTP requests',
              ['method', 'endpoint', 'status']
          )
          
          self.http_request_duration = Histogram(
              'http_request_duration_seconds',
              'HTTP request duration',
              ['method', 'endpoint']
          )
          
          # AI Metrics
          self.ai_requests_total = Counter(
              'ai_requests_total',
              'Total AI requests',
              ['model', 'type']
          )
          
          self.ai_response_duration = Histogram(
              'ai_response_duration_seconds',
              'AI response duration',
              ['model', 'type']
          )
          
          self.ai_tokens_used = Counter(
              'ai_tokens_used_total',
              'Total AI tokens used',
              ['model', 'type']
          )
          
          # Chat Metrics
          self.chat_sessions_active = Gauge(
              'chat_sessions_active',
              'Active chat sessions'
          )
          
          self.chat_messages_total = Counter(
              'chat_messages_total',
              'Total chat messages',
              ['user_type']
          )
          
          # RAG Metrics
          self.rag_queries_total = Counter(
              'rag_queries_total',
              'Total RAG queries'
          )
          
          self.rag_query_success_rate = Gauge(
              'rag_query_success_rate',
              'RAG query success rate'
          )
          
          self.vector_search_duration = Histogram(
              'vector_search_duration_seconds',
              'Vector search duration'
          )
          
          # Indexing Metrics
          self.indexing_jobs_total = Counter(
              'indexing_jobs_total',
              'Total indexing jobs',
              ['status']
          )
          
          self.indexing_files_processed = Counter(
              'indexing_files_processed_total',
              'Total files processed',
              ['format', 'status']
          )
          
          self.indexing_duration = Histogram(
              'indexing_duration_seconds',
              'Indexing job duration'
          )
          
          # System Metrics
          self.active_users = Gauge(
              'active_users_total',
              'Total active users'
          )
          
          self.database_operations = Counter(
              'database_operations_total',
              'Database operations',
              ['operation', 'collection']
          )
          
          self.database_duration = Histogram(
              'database_duration_seconds',
              'Database operation duration',
              ['operation', 'collection']
          )
      
      def track_http_request(self, method: str, endpoint: str, status: int, duration: float):
          """Track HTTP request metrics"""
          self.http_requests_total.labels(
              method=method, 
              endpoint=endpoint, 
              status=str(status)
          ).inc()
          
          self.http_request_duration.labels(
              method=method, 
              endpoint=endpoint
          ).observe(duration)
      
      def track_ai_request(self, model: str, request_type: str, duration: float, tokens: int):
          """Track AI request metrics"""
          self.ai_requests_total.labels(model=model, type=request_type).inc()
          self.ai_response_duration.labels(model=model, type=request_type).observe(duration)
          self.ai_tokens_used.labels(model=model, type=request_type).inc(tokens)
      
      def track_chat_activity(self, message_count: int, active_sessions: int):
          """Track chat activity"""
          self.chat_messages_total.labels(user_type='human').inc(message_count)
          self.chat_sessions_active.set(active_sessions)
      
      def track_rag_query(self, duration: float, success: bool):
          """Track RAG query metrics"""
          self.rag_queries_total.inc()
          self.vector_search_duration.observe(duration)
          
          # Update success rate (simplified - in production, use sliding window)
          current_rate = self.rag_query_success_rate._value._value
          if success:
              self.rag_query_success_rate.set(min(1.0, current_rate + 0.01))
          else:
              self.rag_query_success_rate.set(max(0.0, current_rate - 0.01))
      
      def track_indexing_job(self, status: str, duration: Optional[float] = None):
          """Track indexing job metrics"""
          self.indexing_jobs_total.labels(status=status).inc()
          if duration:
              self.indexing_duration.observe(duration)
      
      def track_file_processing(self, file_format: str, status: str):
          """Track file processing metrics"""
          self.indexing_files_processed.labels(format=file_format, status=status).inc()
      
      def track_database_operation(self, operation: str, collection: str, duration: float):
          """Track database operation metrics"""
          self.database_operations.labels(operation=operation, collection=collection).inc()
          self.database_duration.labels(operation=operation, collection=collection).observe(duration)
      
      def update_active_users(self, count: int):
          """Update active users count"""
          self.active_users.set(count)
  
  # Global metrics instance
  metrics = MetricsService()
  
  # Decorators for automatic metrics collection
  def track_endpoint_metrics(endpoint_name: str):
      """Decorator to automatically track endpoint metrics"""
      def decorator(func):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              start_time = time.time()
              status = 200
              
              try:
                  result = await func(*args, **kwargs)
                  return result
              except Exception as e:
                  status = 500
                  raise
              finally:
                  duration = time.time() - start_time
                  # Get method from request context
                  method = getattr(kwargs.get('request', {}), 'method', 'GET')
                  metrics.track_http_request(method, endpoint_name, status, duration)
          
          return wrapper
      return decorator
  
  def track_ai_metrics(model: str, request_type: str):
      """Decorator to track AI request metrics"""
      def decorator(func):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              start_time = time.time()
              
              result = await func(*args, **kwargs)
              
              duration = time.time() - start_time
              tokens = getattr(result, 'tokens_used', 0)
              
              metrics.track_ai_request(model, request_type, duration, tokens)
              
              return result
          
          return wrapper
      return decorator
  ```

- [ ] **Health Check Service**
  ```python
  # backend/app/services/health_service.py
  import asyncio
  from typing import Dict, Any, List
  import aiohttp
  from qdrant_client import QdrantClient
  import time
  
  class HealthCheckService:
      def __init__(self):
          self.checks = {
              'database': self._check_mongodb,
              'vector_store': self._check_qdrant,
              'ai_service': self._check_azure_ai,
              'disk_space': self._check_disk_space,
              'memory_usage': self._check_memory_usage,
          }
      
      async def get_system_health(self) -> Dict[str, Any]:
          """Get comprehensive system health status"""
          health_status = {
              'status': 'healthy',
              'timestamp': time.time(),
              'checks': {},
              'overall_score': 0
          }
          
          # Run all health checks
          check_results = await asyncio.gather(*[
              self._run_check(name, check_func) 
              for name, check_func in self.checks.items()
          ], return_exceptions=True)
          
          # Process results
          healthy_checks = 0
          total_checks = len(self.checks)
          
          for i, (name, _) in enumerate(self.checks.items()):
              result = check_results[i]
              
              if isinstance(result, Exception):
                  health_status['checks'][name] = {
                      'status': 'error',
                      'message': str(result),
                      'response_time': None
                  }
              else:
                  health_status['checks'][name] = result
                  if result['status'] == 'healthy':
                      healthy_checks += 1
          
          # Calculate overall status
          health_status['overall_score'] = (healthy_checks / total_checks) * 100
          
          if health_status['overall_score'] >= 90:
              health_status['status'] = 'healthy'
          elif health_status['overall_score'] >= 70:
              health_status['status'] = 'degraded'
          else:
              health_status['status'] = 'unhealthy'
          
          return health_status
      
      async def _run_check(self, name: str, check_func) -> Dict[str, Any]:
          """Run individual health check with timing"""
          start_time = time.time()
          
          try:
              result = await check_func()
              response_time = time.time() - start_time
              
              return {
                  'status': 'healthy' if result else 'unhealthy',
                  'response_time': response_time,
                  'message': 'OK' if result else 'Check failed',
                  'details': result if isinstance(result, dict) else None
              }
          except Exception as e:
              response_time = time.time() - start_time
              return {
                  'status': 'error',
                  'response_time': response_time,
                  'message': str(e),
                  'details': None
              }
      
      async def _check_mongodb(self) -> bool:
          """Check MongoDB connection"""
          try:
              result = await MongoDB.database.command('ping')
              return result.get('ok') == 1
          except Exception:
              return False
      
      async def _check_qdrant(self) -> bool:
          """Check Qdrant connection"""
          try:
              client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
              collections = await client.get_collections()
              return len(collections.collections) >= 0
          except Exception:
              return False
      
      async def _check_azure_ai(self) -> Dict[str, Any]:
          """Check Azure AI service"""
          try:
              # Simple test request
              async with aiohttp.ClientSession() as session:
                  headers = {
                      'api-key': settings.AZURE_OPENAI_KEY,
                      'Content-Type': 'application/json'
                  }
                  
                  test_data = {
                      'messages': [{'role': 'user', 'content': 'test'}],
                      'max_tokens': 1
                  }
                  
                  async with session.post(
                      f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version=2023-12-01-preview",
                      headers=headers,
                      json=test_data,
                      timeout=aiohttp.ClientTimeout(total=10)
                  ) as response:
                      return {
                          'status_code': response.status,
                          'available': response.status == 200
                      }
          except Exception as e:
              return {'available': False, 'error': str(e)}
      
      async def _check_disk_space(self) -> Dict[str, Any]:
          """Check available disk space"""
          import shutil
          
          try:
              total, used, free = shutil.disk_usage('/')
              
              free_percent = (free / total) * 100
              
              return {
                  'total_gb': round(total / (1024**3), 2),
                  'used_gb': round(used / (1024**3), 2),
                  'free_gb': round(free / (1024**3), 2),
                  'free_percent': round(free_percent, 2),
                  'healthy': free_percent > 10  # Alert if less than 10% free
              }
          except Exception:
              return {'healthy': False}
      
      async def _check_memory_usage(self) -> Dict[str, Any]:
          """Check memory usage"""
          import psutil
          
          try:
              memory = psutil.virtual_memory()
              
              return {
                  'total_gb': round(memory.total / (1024**3), 2),
                  'used_gb': round(memory.used / (1024**3), 2),
                  'available_gb': round(memory.available / (1024**3), 2),
                  'percent_used': memory.percent,
                  'healthy': memory.percent < 85  # Alert if more than 85% used
              }
          except Exception:
              return {'healthy': False}
  ```

### 3. Alerting Configuration

- [ ] **Grafana Alerting Rules**
  ```yaml
  # monitoring/grafana/provisioning/alerting/rules.yml
  groups:
    - name: system_alerts
      interval: 1m
      rules:
        - alert: HighErrorRate
          expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "High error rate detected"
            description: "Error rate is {{ $value }} errors per second"
        
        - alert: HighResponseTime
          expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High response time detected"
            description: "95th percentile response time is {{ $value }}s"
        
        - alert: LowDiskSpace
          expr: disk_free_percent < 10
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Low disk space"
            description: "Disk space is {{ $value }}% full"
        
        - alert: HighMemoryUsage
          expr: memory_usage_percent > 85
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High memory usage"
            description: "Memory usage is {{ $value }}%"
        
        - alert: IndexingJobsFailing
          expr: rate(indexing_jobs_total{status="failed"}[10m]) > 0.5
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: "High indexing job failure rate"
            description: "{{ $value }} indexing jobs are failing per minute"
        
        - alert: AIServiceDown
          expr: ai_service_health == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "AI service is down"
            description: "Azure AI service is not responding"
  ```

### 4. Log Aggregation Enhancement

- [ ] **Structured Logging Configuration**
  ```python
  # backend/app/core/logging_config.py
  import structlog
  import logging
  import json
  from datetime import datetime
  
  def configure_logging():
      """Configure structured logging for better observability"""
      
      def add_timestamp(_, __, event_dict):
          """Add timestamp to log events"""
          event_dict['timestamp'] = datetime.utcnow().isoformat()
          return event_dict
      
      def add_log_level(_, method_name, event_dict):
          """Add log level to event dict"""
          event_dict['level'] = method_name.upper()
          return event_dict
      
      def serialize_for_loki(_, __, event_dict):
          """Serialize for Loki ingestion"""
          return json.dumps(event_dict, default=str)
      
      # Configure structlog
      structlog.configure(
          processors=[
              structlog.stdlib.filter_by_level,
              structlog.stdlib.add_logger_name,
              add_log_level,
              add_timestamp,
              structlog.processors.StackInfoRenderer(),
              structlog.processors.format_exc_info,
              serialize_for_loki,
          ],
          context_class=dict,
          logger_factory=structlog.stdlib.LoggerFactory(),
          wrapper_class=structlog.stdlib.BoundLogger,
          cache_logger_on_first_use=True,
      )
      
      # Configure Python logging
      logging.basicConfig(
          format="%(message)s",
          level=logging.INFO,
          handlers=[
              logging.FileHandler('/app/logs/application.log'),
              logging.StreamHandler()
          ]
      )
  
  # Application logger with context
  logger = structlog.get_logger("portal_app")
  
  # Context managers for request tracing
  class RequestContext:
      def __init__(self, request_id: str, user_id: str = None):
          self.request_id = request_id
          self.user_id = user_id
      
      def __enter__(self):
          self.token = structlog.contextvars.bind_contextvars(
              request_id=self.request_id,
              user_id=self.user_id
          )
          return self
      
      def __exit__(self, exc_type, exc_val, exc_tb):
          structlog.contextvars.unbind_contextvars("request_id", "user_id")
  ```

## 📦 Deliverable

### Monitoring Infrastructure
- [ ] Grafana dashboards personalizzati
- [ ] Prometheus metrics collection
- [ ] Loki log aggregation
- [ ] Alert manager configuration

### Custom Metrics
- [ ] Application-specific metrics
- [ ] Business metrics tracking
- [ ] Performance indicators
- [ ] User experience metrics

### Health Monitoring
- [ ] Comprehensive health checks
- [ ] Service dependency monitoring
- [ ] Resource utilization tracking
- [ ] Automated alerting system

### Analytics & Reporting
- [ ] Usage analytics dashboards
- [ ] Performance trend analysis
- [ ] Error tracking e analysis
- [ ] Capacity planning metrics

## ✅ Criteri di Completamento

### Monitoring Coverage
- ✅ All system components monitored
- ✅ Business metrics tracked
- ✅ Performance baselines established
- ✅ Alert thresholds configured

### Observability
- ✅ Distributed tracing implementato
- ✅ Structured logging in place
- ✅ Correlation IDs per requests
- ✅ Debug capabilities enhanced

### Alerting
- ✅ Critical alerts configured
- ✅ Escalation procedures defined
- ✅ False positive minimization
- ✅ Alert fatigue prevention

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: DevOps & Monitoring Team* 
