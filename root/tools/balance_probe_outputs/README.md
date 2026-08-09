# Balance Probe Outputs

Run the tracked probe from the repository root:

```powershell
.\.venv\Scripts\python.exe tools\balance_probe.py
```

Each completed run creates one ignored directory named `YYYY-MM-DD_HH-MM-SS`
under `tools/balance_probe_outputs`. It contains a Markdown report, raw results
JSON, and metadata JSON using the same run ID in each filename. Generated runs
are intentionally ignored so the local output history can be retained and
zipped for later balance review.

To package the complete local history, create an archive of the
`tools/balance_probe_outputs` directory while retaining this README.
