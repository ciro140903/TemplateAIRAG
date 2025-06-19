# 📚 FASE 07: SISTEMA INDICIZZAZIONE

## 📋 Panoramica Fase

Implementazione del sistema completo di indicizzazione documenti con job scheduler, monitoring UI, supporto multi-formato, e gestione avanzata delle configurazioni di indicizzazione.

## 🎯 Obiettivi

- **Job Scheduler Robusto**: Indicizzazione automatica e manuale
- **Multi-Format Processing**: Supporto esteso formati documenti
- **Monitoring Avanzato**: Tracking job e performance metrics
- **Configuration UI**: Gestione completa via interfaccia
- **Error Recovery**: Resilienza e retry logic

## ⏱️ Timeline

- **Durata Stimata**: 10-12 giorni
- **Priorità**: ⭐⭐ ALTA
- **Dipendenze**: Fase 05 (Sistema RAG), Fase 06 (Pannello Admin)
- **Parallelo con**: Fase 08 (Sicurezza e MFA)

## 🛠️ Task Dettagliati

### 1. Job Scheduler Backend

- [ ] **Indexing Job Manager**
  ```python
  # backend/app/services/indexing_service.py
  import asyncio
  from typing import List, Dict, Optional, AsyncGenerator
  from celery import Celery
  from pathlib import Path
  import aiofiles
  import hashlib
  from datetime import datetime, timedelta
  
  class IndexingJob:
      def __init__(self, job_id: str, config: Dict):
          self.job_id = job_id
          self.config = config
          self.status = "pending"
          self.progress = 0
          self.total_files = 0
          self.processed_files = 0
          self.errors = []
          self.start_time = None
          self.end_time = None
  
  class IndexingService:
      def __init__(self):
          self.rag_service = RAGService()
          self.db = MongoDB.database
          self.jobs_collection = "indexing_jobs"
          self.current_jobs: Dict[str, IndexingJob] = {}
      
      async def start_indexing_job(
          self,
          job_config: Dict,
          user_id: str
      ) -> str:
          """Start a new indexing job"""
          job_id = f"idx_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
          
          job = IndexingJob(job_id, job_config)
          self.current_jobs[job_id] = job
          
          # Save job to database
          await self._save_job_to_db(job, user_id)
          
          # Start background task
          asyncio.create_task(self._execute_indexing_job(job))
          
          return job_id
      
      async def _execute_indexing_job(self, job: IndexingJob):
          """Execute indexing job in background"""
          try:
              job.status = "running"
              job.start_time = datetime.utcnow()
              await self._update_job_status(job)
              
              # Get files to index
              files_to_index = await self._discover_files(job.config)
              job.total_files = len(files_to_index)
              
              await self._update_job_status(job)
              
              # Process files
              async for progress in self._process_files_batch(job, files_to_index):
                  job.progress = progress
                  await self._update_job_status(job)
              
              job.status = "completed"
              job.end_time = datetime.utcnow()
              
          except Exception as e:
              job.status = "failed"
              job.errors.append(str(e))
              job.end_time = datetime.utcnow()
              logger.error(f"Indexing job {job.job_id} failed: {e}")
          
          finally:
              await self._update_job_status(job)
              # Clean up from memory after some time
              asyncio.create_task(self._cleanup_job(job.job_id, delay=3600))
      
      async def _discover_files(self, config: Dict) -> List[str]:
          """Discover files to index based on configuration"""
          base_paths = config.get("paths", ["/mnt"])
          extensions = config.get("extensions", [".pdf", ".docx", ".txt"])
          max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
          excluded_paths = config.get("excluded_paths", [])
          
          files_to_index = []
          
          for base_path in base_paths:
              path_obj = Path(base_path)
              if not path_obj.exists():
                  continue
              
              for ext in extensions:
                  for file_path in path_obj.rglob(f"*{ext}"):
                      # Check if file should be excluded
                      if any(excluded in str(file_path) for excluded in excluded_paths):
                          continue
                      
                      # Check file size
                      if file_path.stat().st_size > max_file_size:
                          continue
                      
                      # Check if file is already indexed (hash-based)
                      if not await self._should_reindex_file(str(file_path)):
                          continue
                      
                      files_to_index.append(str(file_path))
          
          return files_to_index
      
      async def _should_reindex_file(self, file_path: str) -> bool:
          """Check if file should be reindexed based on modification time and hash"""
          file_stat = Path(file_path).stat()
          current_hash = await self._calculate_file_hash(file_path)
          
          # Check if file record exists in database
          existing_record = await self.db.indexed_files.find_one({
              "file_path": file_path
          })
          
          if not existing_record:
              return True
          
          # Check if file has changed
          if (existing_record.get("file_hash") != current_hash or
              existing_record.get("modified_time") != file_stat.st_mtime):
              return True
          
          return False
      
      async def _calculate_file_hash(self, file_path: str) -> str:
          """Calculate SHA256 hash of file"""
          hash_sha256 = hashlib.sha256()
          async with aiofiles.open(file_path, 'rb') as f:
              async for chunk in f:
                  hash_sha256.update(chunk)
          return hash_sha256.hexdigest()
      
      async def _process_files_batch(
          self, 
          job: IndexingJob, 
          files: List[str]
      ) -> AsyncGenerator[float, None]:
          """Process files in batches"""
          batch_size = job.config.get("batch_size", 10)
          
          for i in range(0, len(files), batch_size):
              batch = files[i:i + batch_size]
              
              # Process batch
              tasks = [self._index_single_file(file_path, job) for file_path in batch]
              results = await asyncio.gather(*tasks, return_exceptions=True)
              
              # Update progress
              for j, result in enumerate(results):
                  if isinstance(result, Exception):
                      job.errors.append(f"Error processing {batch[j]}: {str(result)}")
                  else:
                      job.processed_files += 1
              
              # Yield progress
              progress = (job.processed_files / job.total_files) * 100
              yield progress
              
              # Small delay to prevent overwhelming the system
              await asyncio.sleep(0.1)
      
      async def _index_single_file(self, file_path: str, job: IndexingJob) -> bool:
          """Index a single file"""
          try:
              document_id = f"doc_{hashlib.md5(file_path.encode()).hexdigest()}"
              
              # Index document using RAG service
              result = await self.rag_service.index_document(
                  file_path=file_path,
                  document_id=document_id,
                  metadata={
                      "indexed_by_job": job.job_id,
                      "indexed_by_user": job.config.get("user_id"),
                  }
              )
              
              # Update file record in database
              file_stat = Path(file_path).stat()
              file_hash = await self._calculate_file_hash(file_path)
              
              await self.db.indexed_files.update_one(
                  {"file_path": file_path},
                  {
                      "$set": {
                          "document_id": document_id,
                          "file_hash": file_hash,
                          "modified_time": file_stat.st_mtime,
                          "indexed_at": datetime.utcnow(),
                          "indexing_job_id": job.job_id,
                          "chunks_count": result.get("chunks_count", 0),
                          "status": "indexed"
                      }
                  },
                  upsert=True
              )
              
              return True
              
          except Exception as e:
              logger.error(f"Error indexing file {file_path}: {e}")
              raise
      
      async def get_job_status(self, job_id: str) -> Optional[Dict]:
          """Get current job status"""
          if job_id in self.current_jobs:
              job = self.current_jobs[job_id]
              return {
                  "job_id": job_id,
                  "status": job.status,
                  "progress": job.progress,
                  "total_files": job.total_files,
                  "processed_files": job.processed_files,
                  "errors_count": len(job.errors),
                  "start_time": job.start_time.isoformat() if job.start_time else None,
                  "end_time": job.end_time.isoformat() if job.end_time else None,
              }
          
          # Check database for completed jobs
          job_record = await self.db[self.jobs_collection].find_one({"job_id": job_id})
          if job_record:
              return {
                  "job_id": job_id,
                  "status": job_record.get("status"),
                  "progress": job_record.get("progress", 0),
                  "total_files": job_record.get("total_files", 0),
                  "processed_files": job_record.get("processed_files", 0),
                  "errors_count": len(job_record.get("errors", [])),
                  "start_time": job_record.get("start_time"),
                  "end_time": job_record.get("end_time"),
              }
          
          return None
      
      async def list_indexing_jobs(
          self, 
          limit: int = 50, 
          status_filter: Optional[str] = None
      ) -> List[Dict]:
          """List indexing jobs with optional status filter"""
          query = {}
          if status_filter:
              query["status"] = status_filter
          
          cursor = self.db[self.jobs_collection].find(query).sort("start_time", -1).limit(limit)
          jobs = []
          async for doc in cursor:
              jobs.append({
                  "job_id": doc["job_id"],
                  "status": doc["status"],
                  "progress": doc.get("progress", 0),
                  "total_files": doc.get("total_files", 0),
                  "processed_files": doc.get("processed_files", 0),
                  "errors_count": len(doc.get("errors", [])),
                  "start_time": doc.get("start_time"),
                  "end_time": doc.get("end_time"),
                  "config": doc.get("config", {}),
              })
          
          return jobs
      
      async def cancel_job(self, job_id: str) -> bool:
          """Cancel a running job"""
          if job_id in self.current_jobs:
              job = self.current_jobs[job_id]
              if job.status == "running":
                  job.status = "cancelled"
                  job.end_time = datetime.utcnow()
                  await self._update_job_status(job)
                  return True
          
          return False
      
      async def get_indexing_statistics(self) -> Dict:
          """Get indexing statistics"""
          total_jobs = await self.db[self.jobs_collection].count_documents({})
          completed_jobs = await self.db[self.jobs_collection].count_documents({"status": "completed"})
          failed_jobs = await self.db[self.jobs_collection].count_documents({"status": "failed"})
          running_jobs = len([j for j in self.current_jobs.values() if j.status == "running"])
          
          total_files = await self.db.indexed_files.count_documents({})
          
          # Recent activity (last 7 days)
          week_ago = datetime.utcnow() - timedelta(days=7)
          recent_jobs = await self.db[self.jobs_collection].count_documents({
              "start_time": {"$gte": week_ago}
          })
          
          return {
              "total_jobs": total_jobs,
              "completed_jobs": completed_jobs,
              "failed_jobs": failed_jobs,
              "running_jobs": running_jobs,
              "total_indexed_files": total_files,
              "recent_jobs_week": recent_jobs,
              "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
          }
  ```

### 2. Frontend Indexing Management

- [ ] **Indexing Dashboard Component**
  ```typescript
  // src/components/admin/IndexingDashboard.tsx
  import { useState, useEffect } from 'react';
  import {
    Stack,
    Card,
    ProgressIndicator,
    CommandBar,
    DetailsList,
    IColumn,
    MessageBar,
    MessageBarType,
    Dialog,
    PrimaryButton,
    DefaultButton,
  } from '@fluentui/react';
  import { motion } from 'framer-motion';
  import { useIndexingStore } from '@/store/indexingStore';
  import { IndexingConfigForm } from './IndexingConfigForm';
  import { JobDetailsPanel } from './JobDetailsPanel';
  
  interface IndexingJob {
    job_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
    progress: number;
    total_files: number;
    processed_files: number;
    errors_count: number;
    start_time?: string;
    end_time?: string;
  }
  
  export const IndexingDashboard: React.FC = () => {
    const [showConfigDialog, setShowConfigDialog] = useState(false);
    const [selectedJob, setSelectedJob] = useState<IndexingJob | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    
    const {
      jobs,
      statistics,
      isLoading,
      error,
      loadJobs,
      loadStatistics,
      startIndexingJob,
      cancelJob,
      getJobDetails,
    } = useIndexingStore();
    
    useEffect(() => {
      loadJobs();
      loadStatistics();
    }, [loadJobs, loadStatistics]);
    
    useEffect(() => {
      let interval: NodeJS.Timeout;
      
      if (autoRefresh) {
        interval = setInterval(() => {
          loadJobs();
          loadStatistics();
        }, 5000); // Refresh every 5 seconds
      }
      
      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    }, [autoRefresh, loadJobs, loadStatistics]);
    
    const commandBarItems = [
      {
        key: 'new-job',
        text: 'Nuova Indicizzazione',
        iconProps: { iconName: 'Add' },
        onClick: () => setShowConfigDialog(true),
      },
      {
        key: 'refresh',
        text: 'Aggiorna',
        iconProps: { iconName: 'Refresh' },
        onClick: () => {
          loadJobs();
          loadStatistics();
        },
      },
      {
        key: 'auto-refresh',
        text: autoRefresh ? 'Disabilita Auto-refresh' : 'Abilita Auto-refresh',
        iconProps: { iconName: autoRefresh ? 'Pause' : 'Play' },
        onClick: () => setAutoRefresh(!autoRefresh),
      },
    ];
    
    const jobColumns: IColumn[] = [
      {
        key: 'job_id',
        name: 'Job ID',
        fieldName: 'job_id',
        minWidth: 150,
        maxWidth: 200,
        onRender: (item: IndexingJob) => (
          <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
            {item.job_id.substring(0, 20)}...
          </span>
        ),
      },
      {
        key: 'status',
        name: 'Stato',
        fieldName: 'status',
        minWidth: 100,
        maxWidth: 120,
        onRender: (item: IndexingJob) => {
          const statusColors = {
            pending: '#6c757d',
            running: '#0078d4',
            completed: '#107c10',
            failed: '#d13438',
            cancelled: '#ff8c00',
          };
          
          return (
            <span
              style={{
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: statusColors[item.status],
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold',
              }}
            >
              {item.status.toUpperCase()}
            </span>
          );
        },
      },
      {
        key: 'progress',
        name: 'Progresso',
        fieldName: 'progress',
        minWidth: 150,
        maxWidth: 200,
        onRender: (item: IndexingJob) => (
          <ProgressIndicator
            percentComplete={item.progress / 100}
            description={`${item.processed_files}/${item.total_files} files`}
          />
        ),
      },
      {
        key: 'start_time',
        name: 'Inizio',
        fieldName: 'start_time',
        minWidth: 120,
        maxWidth: 150,
        onRender: (item: IndexingJob) =>
          item.start_time ? new Date(item.start_time).toLocaleString('it-IT') : '-',
      },
      {
        key: 'duration',
        name: 'Durata',
        minWidth: 100,
        maxWidth: 120,
        onRender: (item: IndexingJob) => {
          if (!item.start_time) return '-';
          
          const start = new Date(item.start_time);
          const end = item.end_time ? new Date(item.end_time) : new Date();
          const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
          
          if (duration < 60) return `${duration}s`;
          if (duration < 3600) return `${Math.floor(duration / 60)}m`;
          return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
        },
      },
      {
        key: 'errors',
        name: 'Errori',
        fieldName: 'errors_count',
        minWidth: 80,
        maxWidth: 100,
        onRender: (item: IndexingJob) => (
          <span style={{ color: item.errors_count > 0 ? '#d13438' : '#107c10' }}>
            {item.errors_count}
          </span>
        ),
      },
    ];
    
    const handleJobSelection = async (job: IndexingJob) => {
      const details = await getJobDetails(job.job_id);
      setSelectedJob(details);
    };
    
    const handleCancelJob = async (jobId: string) => {
      if (window.confirm('Sei sicuro di voler annullare questo job?')) {
        await cancelJob(jobId);
        loadJobs();
      }
    };
    
    return (
      <Stack tokens={{ childrenGap: 24 }}>
        <h1>Dashboard Indicizzazione</h1>
        
        {error && (
          <MessageBar messageBarType={MessageBarType.error}>
            {error}
          </MessageBar>
        )}
        
        {/* Statistics Cards */}
        <Stack horizontal tokens={{ childrenGap: 16 }} wrap>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card
              styles={{
                root: {
                  width: 200,
                  padding: '16px',
                  backgroundColor: '#0078d4',
                  color: 'white',
                },
              }}
            >
              <Stack tokens={{ childrenGap: 8 }}>
                <h3 style={{ margin: 0 }}>Jobs Totali</h3>
                <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {statistics?.total_jobs || 0}
                </span>
              </Stack>
            </Card>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card
              styles={{
                root: {
                  width: 200,
                  padding: '16px',
                  backgroundColor: '#107c10',
                  color: 'white',
                },
              }}
            >
              <Stack tokens={{ childrenGap: 8 }}>
                <h3 style={{ margin: 0 }}>Completati</h3>
                <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {statistics?.completed_jobs || 0}
                </span>
              </Stack>
            </Card>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card
              styles={{
                root: {
                  width: 200,
                  padding: '16px',
                  backgroundColor: '#d13438',
                  color: 'white',
                },
              }}
            >
              <Stack tokens={{ childrenGap: 8 }}>
                <h3 style={{ margin: 0 }}>Falliti</h3>
                <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {statistics?.failed_jobs || 0}
                </span>
              </Stack>
            </Card>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Card
              styles={{
                root: {
                  width: 200,
                  padding: '16px',
                  backgroundColor: '#ff8c00',
                  color: 'white',
                },
              }}
            >
              <Stack tokens={{ childrenGap: 8 }}>
                <h3 style={{ margin: 0 }}>In Esecuzione</h3>
                <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {statistics?.running_jobs || 0}
                </span>
              </Stack>
            </Card>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <Card
              styles={{
                root: {
                  width: 200,
                  padding: '16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                },
              }}
            >
              <Stack tokens={{ childrenGap: 8 }}>
                <h3 style={{ margin: 0 }}>File Indicizzati</h3>
                <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {statistics?.total_indexed_files || 0}
                </span>
              </Stack>
            </Card>
          </motion.div>
        </Stack>
        
        {/* Command Bar */}
        <CommandBar items={commandBarItems} />
        
        {/* Jobs List */}
        <DetailsList
          items={jobs}
          columns={jobColumns}
          setKey="set"
          layoutMode={0}
          onItemInvoked={handleJobSelection}
        />
        
        {/* New Job Dialog */}
        <Dialog
          hidden={!showConfigDialog}
          onDismiss={() => setShowConfigDialog(false)}
          dialogContentProps={{
            title: 'Configura Nuova Indicizzazione',
            subText: 'Imposta i parametri per la nuova indicizzazione',
          }}
          modalProps={{ isBlocking: true }}
          maxWidth="600px"
        >
          <IndexingConfigForm
            onSubmit={async (config) => {
              await startIndexingJob(config);
              setShowConfigDialog(false);
              loadJobs();
            }}
            onCancel={() => setShowConfigDialog(false)}
          />
        </Dialog>
        
        {/* Job Details Panel */}
        {selectedJob && (
          <JobDetailsPanel
            job={selectedJob}
            onClose={() => setSelectedJob(null)}
            onCancel={handleCancelJob}
          />
        )}
      </Stack>
    );
  };
  ```

## 📦 Deliverable

### Backend Components
- [ ] Job scheduler con async processing
- [ ] File discovery e filtering logic
- [ ] Batch processing ottimizzato
- [ ] Error handling e recovery

### Frontend Components
- [ ] Indexing dashboard con real-time updates
- [ ] Job configuration interface
- [ ] Progress monitoring UI
- [ ] Error reporting e logs viewer

### Configuration Management
- [ ] Path selection e filtering
- [ ] File type configuration
- [ ] Batch size e performance tuning
- [ ] Schedule automation

### Monitoring & Analytics
- [ ] Real-time job progress
- [ ] Performance metrics
- [ ] Error tracking e analysis
- [ ] Historical data e trends

## ✅ Criteri di Completamento

### Funzionali
- ✅ Job scheduling automatico e manuale
- ✅ Multi-format file processing
- ✅ Real-time progress monitoring
- ✅ Error recovery e retry logic

### Performance
- ✅ Batch processing efficiente
- ✅ Memory usage ottimizzato
- ✅ Concurrent job support
- ✅ Large dataset handling

### Reliability
- ✅ Job persistence attraverso restart
- ✅ Error logging completo
- ✅ Resume capability per job interrotti
- ✅ Health checks e monitoring

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Indexing & Processing Team*