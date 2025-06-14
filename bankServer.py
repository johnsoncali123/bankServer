from flask import Flask, request, jsonify, render_template_string, abort
from collections import defaultdict
app = Flask(__name__)
message_queues = defaultdict(list)
terminal_notice = None
HTML_FORM = """
<!doctype html>
<title>Send Message</title>
<img src="{{ url_for('static', filename='KC.png') }}" alt="Logo" style="height: 80px;">

<form method="post">
  <label>TO:</label><br>
  <input type="number" name="to" required><br><br>
  
  <label>DATA:</label><br>
  <input type="text" name="data" required><br><br>

  <input type="submit" value="SEND">
</form>

<hr>
<div style="color:blue" id="terminal-output">
  <!-- leave empty; JS will populate this -->
</div>

<script>
setInterval(() => {
  fetch("/terminal/status")
    .then(res => res.json())
    .then(data => {
      console.log("terminal/status payload:", data);
      const container = document.getElementById("terminal-output");
      container.innerHTML = "";

      // If there's no notice key or it's empty, bail out
      if (!data.notice || data.notice.length === 0) {
        return;
      }

      // Normalize to an array
      let lines = [];
      if (Array.isArray(data.notice)) {
        lines = data.notice;
      } else if (typeof data.notice === "string") {
        try {
          lines = JSON.parse(data.notice);
        } catch (e) {
          console.warn("Could not JSON.parse notice, skipping:", data.notice);
          return;
        }
      } else {
        console.warn("Unexpected notice type:", typeof data.notice);
        return;
      }

      // Render, skipping the "Select an option." prompt
      lines.forEach(line => {
        if (line === "Select an option.") return;
        const p = document.createElement("p");
        p.textContent = line;
        container.appendChild(p);
      });
    })
    .catch(err => console.error("Error polling /terminal/status:", err));
}, 1000);
</script>
"""
@app.route('/bankofeuropemain', methods=['GET'])
def main_queue():
    queue = message_queues[3000]
    messages = queue[:]
    message_queues[3000] = []
    return jsonify(messages), 200
@app.route('/receive/3000', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def receive_3000_forbidden():
    abort(404)
@app.route('/receive/<int:receiver_id>', methods=['GET'])
def receive_message(receiver_id):
    queue = message_queues[receiver_id]
    messages = queue[:]
    message_queues[receiver_id] = []
    return jsonify(messages), 200
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
            received = data.get("data")
            if isinstance(received, list):
                terminal_notice = received
            else:
                terminal_notice = [str(received)]
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Send Error:", e)
        return jsonify({"error": "Invalid JSON"}), 400
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
    return render_template_string(HTML_FORM, message=message, notice=terminal_notice)
@app.route('/terminal/status')
def terminal_status():
    return jsonify({"notice": terminal_notice or []})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)