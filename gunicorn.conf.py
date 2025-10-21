"""
Gunicorn configuration optimized for Charter Pool on OpenBSD.
Production-ready settings for maximum performance.
"""

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'  # Use 'gevent' or 'eventlet' for async if needed
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once
timeout = 30
keepalive = 5

# Performance tuning
preload_app = True  # Load application before forking workers (saves memory)
reuse_port = True  # Use SO_REUSEPORT for better load distribution

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'charter_pool'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("[INFO] Starting Charter Pool server...")

def on_reload(server):
    """Called to recycle workers during a reload."""
    print("[INFO] Reloading Charter Pool server...")

def when_ready(server):
    """Called just after the server is started."""
    print("[INFO] Charter Pool server is ready. Accepting connections.")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"[INFO] Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("[INFO] Forked new master process")

def on_exit(server):
    """Called just before exiting."""
    print("[INFO] Charter Pool server shutdown complete")

# Environment variables
raw_env = [
    'FLASK_ENV=production',
]

# OpenBSD-specific optimizations
# These settings work well with OpenBSD's process scheduling and memory management
#
# To further optimize for OpenBSD:
# 1. Increase file descriptor limits: sysctl kern.maxfiles=20000
# 2. Tune network stack: sysctl net.inet.tcp.sendspace=65536
# 3. Optimize for PostgreSQL: sysctl kern.seminfo.semmni=256
# 4. Enable performance mode: sysctl hw.perfpolicy=high
#
# Add to /etc/sysctl.conf:
#   kern.maxfiles=20000
#   kern.maxproc=4096
#   kern.seminfo.semmni=256
#   kern.seminfo.semmns=512
#   net.inet.tcp.sendspace=65536
#   net.inet.tcp.recvspace=65536
#   hw.perfpolicy=high

