#!/bin/zsh
# Sequential job queue: runs lines of queue.txt one at a time (each job uses <= 4 MPI ranks).
# Finished lines are appended to queue_done.txt with wall time. Edit queue.txt to add jobs while running.
cd /Users/thegreat/Documents/MATLAB/cdte-device-model/dft/interface
PY=/Users/thegreat/Documents/MATLAB/cdte-device-model/.venv/bin/python
while true; do
  # wait for any pw.x/projwfc.x of ours still running (e.g. a job started by hand)
  while pgrep -f "qe-env/bin/(pw|pp|projwfc|average)[.]x|python (run_superlattice|run_bulk_set|bulk_refs|sl_core_levels|homojunction|pseudomorphic|make_superlattice)[.]py" >/dev/null; do sleep 20; done
  line=$(grep -v '^\s*$' queue.txt | grep -v '^#' | head -1)
  [[ -z "$line" ]] && { echo "$(date '+%F %T') queue empty"; sleep 60; continue; }
  # remove that line from queue.txt (first occurrence)
  $PY -c "import sys;p='queue.txt';L=open(p).read().split('\n');i=L.index(sys.argv[1]);L.pop(i);open(p,'w').write('\n'.join(L))" "$line"
  t0=$(date +%s); echo "$(date '+%F %T') START $line"
  eval "$PY $line" >> logs/queue_jobs.log 2>&1; rc=$?
  t1=$(date +%s); echo "$(date '+%F %T') END rc=$rc $((t1-t0))s $line"
  echo "$(date '+%F %T') rc=$rc wall=$((t1-t0))s $line" >> queue_done.txt
done
