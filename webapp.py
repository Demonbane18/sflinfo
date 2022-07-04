from app import create_app

app = create_app()
# app.run(debug=True)

@app.shell_context_processor
def make_shell_context():
    return {}
