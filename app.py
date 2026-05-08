from flask import Flask, request, jsonify, render_template
from model import predict
import random

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/detect', methods=['POST'])
def detect_anomaly():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    try:
        # Simulate a network connection if 'simulate' flag is true
        if data.get('simulate', False):
            # Realistic 'normal' web traffic profile matching KDD Cup baseline
            synthetic_data = {
                'duration': 0,
                'protocol_type': 'tcp',
                'service': 'http',
                'flag': 'SF',
                'src_bytes': random.randint(180, 250),
                'dst_bytes': random.randint(3000, 8000),
                'logged_in': 1,
                'count': random.randint(1, 10),
                'srv_count': random.randint(1, 10),
                'same_srv_rate': 1.0,
                'dst_host_count': random.randint(5, 15),
                'dst_host_srv_count': random.randint(5, 15),
                'dst_host_same_srv_rate': 1.0,
                'dst_host_same_src_port_rate': 0.11
            }
            # Inject a clear anomaly pattern if requested
            if data.get('force_anomaly', False):
                synthetic_data['src_bytes'] = random.randint(100000, 9999999)
                synthetic_data['dst_bytes'] = 0
                synthetic_data['duration'] = random.randint(1000, 9999)
                synthetic_data['count'] = random.randint(300, 500)
                synthetic_data['protocol_type'] = 'icmp'
                synthetic_data['service'] = 'ecr_i'
                synthetic_data['flag'] = 'S0'
                
            data_to_predict = synthetic_data
        else:
            data_to_predict = data.get('features', {})
            
        prediction = predict(data_to_predict)
        
        if prediction is None:
            return jsonify({'error': 'Model not trained'}), 500
            
        result_label = 'Normal' if prediction[0] == 1 else 'Anomaly'
        
        return jsonify({
            'status': 'success',
            'prediction': result_label,
            'features_used': data_to_predict
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "running"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
