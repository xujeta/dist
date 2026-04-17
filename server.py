from flask import Flask, request, jsonify
import cv2
import numpy as np
import json
from terrain.profile_extractor import TerrainProfileExtractor

app = Flask(__name__)

@app.route('/')
def index():
    return "SERVER OK"

@app.route('/process_profile', methods=['POST'])
def process_profile():
    try:
        file = request.files['image']
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        ax, ay = float(request.form['a_x']), float(request.form['a_y'])
        bx, by = float(request.form['b_x']), float(request.form['b_y'])
        h_a, h_b = float(request.form['h_a']), float(request.form['h_b'])
        step = float(request.form['step'])
        
        extrema_str = request.form.get('extrema', '[]')
        extrema = json.loads(extrema_str)

        extractor = TerrainProfileExtractor(step=step, mode="gray")
        
        result = extractor.extract_profile(
            img_bgr=img_bgr, 
            point_a=(ax, ay),
            point_b=(bx, by),
            height_a=h_a,
            height_b=h_b,
            extrema=extrema
        )
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400

        return jsonify({
            "profile_data": result["profile_data"]
        })

    except Exception as e:
        print("ОШИБКА СЕРВЕРА:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
