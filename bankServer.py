from flask import Flask, request, jsonify
from collections import defaultdict

app = Flask(__name__)

# Store messages by receiver ID
message_queues = defaultdict(list)

@app.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json(force=True)
        receiver_id = data.get("to")
        if receiver_id is None:
            return jsonify({"error": "'to' field is required"}), 400
        
        # Store the message in the recipient's queue
        message_queues[receiver_id].append(data)
        print(f"Message for {receiver_id}: {data}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Send Error:", e)
        return jsonify({"error": "Invalid JSON"}), 400

@app.route('/receive/<int:receiver_id>', methods=['GET'])
def receive_message(receiver_id):
    queue = message_queues[receiver_id]
    messages = queue[:]
    message_queues[receiver_id] = []  # Clear the queue
    return jsonify(messages), 200  # <-- RETURN A LIST

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)