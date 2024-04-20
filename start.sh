# IF NO ARGUMENT
if [ $# -eq 0 ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip freeze
    export FLASK_APP=main.py
    flask run -h 127.0.0.1 -p 5000
    exit 0
fi

# IF ARGUMENT IS "deploy"
if [ $1 = "deploy" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip freeze
    export FLASK_APP=main.py
    flask run -h 0.0.0.0 -p 5002
    exit 0
fi
