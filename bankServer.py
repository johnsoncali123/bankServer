from flask import Flask, request, jsonify, render_template_string
from collections import defaultdict
app = Flask(__name__)
message_queues = defaultdict(list)
terminal_notice = None
HTML_FORM = """
<!doctype html>
<title>Send Message</title>
<h2>JewNet™</h2>
<form method="post">
  <label>TO:</label><br>
  <input type="number" name="to" required><br><br>
  
  <label>DATA:</label><br>
  <input type="text" name="data" required><br><br>

  <input type="submit" value="SEND">
</form>

{% if message %}
  <p><strong>{{ message }}</strong></p>
{% endif %}
"""
@app.route('/send', methods=['POST'])
def send_message():
    global terminal_notice
    try:
        data = request.get_json(force=True)
        receiver_id = data.get("to")
        if receiver_id is None:
            return jsonify({"error": "'to' field is required"}), 400
        message_queues[receiver_id].append(data)
        print(f"Message for {receiver_id}: {data}")
        if receiver_id == 4000 and data.get("type") == 1:
            terminal_notice = f"Output: {data.get('data')}"
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Send Error:", e)
        return jsonify({"error": "Invalid JSON"}), 400
@app.route('/receive/<int:receiver_id>', methods=['GET'])
def receive_message(receiver_id):
    queue = message_queues[receiver_id]
    messages = queue[:]
    message_queues[receiver_id] = []
    return jsonify(messages), 200
@app.route('/terminal', methods=['GET', 'POST'])
@app.route('/terminal', methods=['GET', 'POST'])
def terminal():
    global terminal_notice
    message = None
    if request.method == 'POST':
        try:
            to = int(request.form['to'])
            msg_type = 0
            data_raw = request.form['data']
            try:
                data = [int(x.strip()) for x in data_raw.split(',')]
            except ValueError:
                data = data_raw.strip()
            packet = {
                "to": to,
                "from": -1,
                "type": msg_type,
                "data": data
            }
            message_queues[to].append(packet)
            print(f"Terminal message for {to}: {packet}")
            message = f"SENT."
        except Exception as e:
            message = f"ERROR: {str(e)}"
    return render_template_string(HTML_FORM + (
        f"<hr><p style='color:green'>{terminal_notice}</p>" if terminal_notice else ""
    ), message=message)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)