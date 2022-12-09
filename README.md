# tool_tf_to_arc
Python script to create architecture csv from TF files.


To run it in a virtual environment: 

```bash
python3 -m venv env
source env/bin/activate
pip install python-hcl2
chmod +x tf_creds_parser.py
./tf_creds_parser.py --iam gcp_resources.tf
```

Use `--iam` option to get "google_project_iam_member" resources, `--bq` to get "google_bigquery_dataset" resources.

Version 0.0.2 searches for 'google_project_iam_member' and 'google_bigquery_dataset' resources.