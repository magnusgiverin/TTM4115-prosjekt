from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <body>
        <h1>Hello, World!</h1>
        <button onclick="buttonClicked('button1')">Button 1</button>
        <button onclick="buttonClicked('button2')">Button 2</button>
        <button onclick="buttonClicked('button3')">Button 3</button>
        <script>
            function buttonClicked(buttonId) {
                fetch('/button-click', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ buttonId: buttonId }),
                })
                .then(response => response.json())
                .then(data => {
                    alert('Response from server: ' + data.message);
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/button-click', methods=['POST'])
def button_click():
    data = request.get_json()
    button_id = data['buttonId']
    # Define your button click handling logic here
    if button_id == 'button1':
        message = 'Button 1 was clicked!'
    elif button_id == 'button2':
        message = 'Button 2 was clicked!'
    elif button_id == 'button3':
        message = 'Button 3 was clicked!'
    else:
        message = 'Unknown button!'
    return jsonify({'message': message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)