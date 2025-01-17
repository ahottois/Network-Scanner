#!/usr/bin/env python3

import nmap
import socket
import netifaces
import threading
import time
from datetime import datetime
import json
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

class NetworkDevice:
    def __init__(self, ip):
        self.ip = ip
        self.hostname = "Unknown"
        self.mac = ""
        self.status = ""
        self.last_seen = ""
        self.device_type = ""
        self.owner = ""
        self.location = ""
        self.notes = ""

devices = {}
device_data = {}

def load_device_data():
    try:
        with open('device_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_device_data(data):
    with open('device_data.json', 'w') as f:
        json.dump(data, f, indent=4)

device_data = load_device_data()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Scanner</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f4f4f4;
            color: #333;
            margin: 0;
            padding: 20px;
        }

        h1 {
            text-align: center;
            margin-bottom: 20px;
            color: #2980b9;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        table th, table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        table th {
            background-color: #2980b9;
            color: white;
        }

        table tr:hover {
            background-color: #f1f1f1;
        }

        .status-badge {
            padding: 5px 10px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }

        .status-badge.online {
            background-color: #2ecc71; /* Vert pour en ligne */
        }

        .status-badge.offline {
            background-color: #e74c3c; /* Rouge pour hors ligne */
        }

        .device-info {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }

        /* Styles pour le modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }

        .modal-content {
            background-color: white;
            margin: 10% auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 500px;
            position: relative;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .close {
            position: absolute;
            right: 20px;
            top: 10px;
            font-size: 28px;
            cursor: pointer;
            color: #aaa;
        }

        .close:hover {
            color: #555;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        .form-group textarea {
            resize: vertical;
        }

        .save-button {
            background: #2980b9;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }

        .save-button:hover {
            background: #21618c;
        }

        @media (max-width: 600px) {
            .modal-content {
                width: 90%;
            }
        }
    </style>
    <script>
        function refreshPage() {
            location.reload();
        }

        setInterval(refreshPage, 30000);

        function openModal(ip) {
            const modal = document.getElementById('deviceModal');
            modal.style.display = 'block';

            fetch(`/api/device/${ip}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('deviceIP').textContent = ip;
                    document.getElementById('deviceType').value = data.device_type || '';
                    document.getElementById('deviceOwner').value = data.owner || '';
                    document.getElementById('deviceLocation').value = data.location || '';
                    document.getElementById('deviceNotes').value = data.notes || '';
                    document.getElementById('saveButton').onclick = () => saveDeviceData(ip);
                });
        }

        function closeModal() {
            document.getElementById('deviceModal').style.display = 'none';
        }

        function saveDeviceData(ip) {
            const data = {
                device_type: document.getElementById('deviceType').value,
                owner: document.getElementById('deviceOwner').value,
                location: document.getElementById('deviceLocation').value,
                notes: document.getElementById('deviceNotes').value
            };

            fetch(`/api/device/${ip}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if(result.status === 'success') {
                    closeModal();
                    refreshPage();
                }
            });
        }

        window.onclick = function(event) {
            const modal = document.getElementById('deviceModal');
            if (event.target == modal) {
                closeModal();
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>Scanner de Réseau</h1>
        <table class="devices-table">
            <thead>
                <tr>
                    <th>IP</th>
                    <th>Nom d'hôte</th>
                    <th>Adresse MAC</th>
                    <th>Statut</th>
                    <th>Type</th>
                    <th>Dernière détection</th>
                </tr>
            </thead>
            <tbody>
                {% for device in devices.values() %}
                <tr onclick="openModal('{{ device.ip }}')">
                    <td>{{ device.ip }}</td>
                    <td>{{ device.hostname }}</td>
                    <td>{{ device.mac }}</td>
                    <td><span class="status-badge {{ device.status }}">{{ device.status }}</span></td>
                    <td>
                        {% if device.ip in device_data %}
                            {{ device_data[device.ip].get('device_type', 'Non spécifié') }}
                        {% else %}
                            Aucune info disponible
                        {% endif %}
                    </td>
                    <td>{{ device.last_seen }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Modal -->
    <div id="deviceModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>Informations sur l'appareil</h2>
            <h3 id="deviceIP"></h3>
            <div class="form-group">
                <label for="deviceType">Type d'appareil</label>
                <select id="deviceType">
                    <option value="">Sélectionner...</option>
                    <option value="Serveur">Serveur</option>
                    <option value="Base de données">Base de données</option>
                    <option value="Ordinateur">Ordinateur</option>
                    <option value="Smartphone">Smartphone</option>
                    <option value="Tablette">Tablette</option>
                    <option value="IoT">IoT</option>
                    <option value="TV">TV</option>
                    <option value="Console">Console de jeu</option>
                    <option value="Autre">Autre</option>
                </select>
            </div>
            <div class="form-group">
                <label for="deviceOwner">Propriétaire</label>
                <input type="text" id="deviceOwner" placeholder="Nom du propriétaire">
            </div>
            <div class="form-group">
                <label for="deviceLocation">Emplacement</label>
                <input type="text" id="deviceLocation" placeholder="Emplacement de l'appareil">
            </div>
            <div class="form-group">
                <label for="deviceNotes">Notes</label>
                <textarea id="deviceNotes" placeholder="Ajouter des notes..."></textarea>
            </div>
            <button class="save-button" id="saveButton">Enregistrer</button>
        </div>
    </div>
</body>
</html>
'''

def get_network_info():
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                ip = addr['addr']
                if not ip.startswith('127.'):
                    return ip, addr['netmask']
    return None, None

def scan_network():
    while True:
        try:
            nm = nmap.PortScanner()
            ip, netmask = get_network_info()
            if ip:
                network = f"{ip}/24"
                print(f"Scanning network: {network}")

                nm.scan(hosts=network, arguments='-sn')
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for host in nm.all_hosts():
                    if host not in devices:
                        devices[host] = NetworkDevice(host)
                    device = devices[host]
                    device.status = 'online' if nm[host].state() == 'up' else 'offline'
                    device.last_seen = current_time
                    
                    # Tentative d'obtenir le nom de l'hôte
                    try:
                        device.hostname = socket.gethostbyaddr(host)[0]
                    except socket.herror:
                        device.hostname = "Unknown"

                    # Récupérer l'adresse MAC
                    device.mac = nm[host]['addresses'].get('mac', '')

                    # Initialiser les données si non présentes
                    if host not in device_data:
                        device_data[host] = {
                            "device_type": "Inconnu",
                            "owner": "Inconnu",
                            "location": "Inconnu",
                            "notes": ""
                        }

                    print(f"Found device: {device.ip} ({device.hostname}) - {device.status}")

            time.sleep(300)

        except Exception as e:
            print(f"Error during scan: {str(e)}")
            time.sleep(60)

@app.route('/api/device/<ip>', methods=['GET'])
def get_device(ip):
    return jsonify(device_data.get(ip, {}))

@app.route('/api/device/<ip>', methods=['POST'])
def update_device(ip):
    data = request.get_json()
    device_data[ip] = data
    save_device_data(device_data)
    return jsonify({"status": "success"})

@app.route('/')
def home():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(HTML_TEMPLATE, devices=devices, current_time=current_time, device_data=device_data)

if __name__ == '__main__':
    try:
        scanner_thread = threading.Thread(target=scan_network, daemon=True)
        scanner_thread.start()

        app.run(host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        print("Arrêt du scanner...")
