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
        self.is_new = False  
        self.is_known = False  

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

def scan_network():
    nm = nmap.PortScanner()
    
    while True:
        try:
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                if interface != 'lo':  # Ignorer l'interface loopback
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr['addr']
                            subnet = ip.rsplit('.', 1)[0] + '.0/24'
                            
                            nm.scan(hosts=subnet, arguments='-sn')
                            
                            for host in nm.all_hosts():
                                try:
                                    hostname = socket.gethostbyaddr(host)[0]
                                except socket.herror:
                                    hostname = "Unknown"

                                if host not in devices:
                                    devices[host] = NetworkDevice(host)
                                    devices[host].is_new = True

                                devices[host].hostname = hostname
                                devices[host].status = 'online' if nm[host].state() == 'up' else 'offline'
                                devices[host].last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                if 'mac' in nm[host]['addresses']:
                                    devices[host].mac = nm[host]['addresses']['mac']

                                # Initialiser les données si non présentes
                                if host not in device_data:
                                    device_data[host] = {
                                        "device_type": "Inconnu",
                                        "owner": "Inconnu",
                                        "location": "Inconnu",
                                        "notes": "",
                                        "is_known": False
                                    }
                                else:
                                    devices[host].is_known = device_data[host].get('is_known', False)

                                print(f"Found device: {devices[host].ip} ({devices[host].hostname}) - {devices[host].status}")

            time.sleep(300)

        except Exception as e:
            print(f"Error during scan: {str(e)}")
            time.sleep(60)

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
            background-color: #2ecc71;
        }

        .status-badge.offline {
            background-color: #e74c3c;
        }

        .new-device {
            color: red;
        }

        .new-device::after {
            content: " !";
            font-weight: bold;
            color: red;
        }

        .known-device {
            color: green;
        }

        .known-device::after {
            content: " ✓";
            font-weight: bold;
            color: green;
        }

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

        .save-button {
            background-color: #2980b9;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }

        .save-button:hover {
            background-color: #2471a3;
        }
    </style>
    <script>
        function openModal(ip) {
            document.getElementById('deviceModal').style.display = 'block';
            
            fetch(`/api/device/${ip}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('deviceIP').textContent = ip;
                    document.getElementById('deviceType').value = data.device_type || '';
                    document.getElementById('deviceOwner').value = data.owner || '';
                    document.getElementById('deviceLocation').value = data.location || '';
                    document.getElementById('deviceNotes').value = data.notes || '';
                    document.getElementById('isKnown').checked = data.is_known || false;
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
                notes: document.getElementById('deviceNotes').value,
                is_known: document.getElementById('isKnown').checked
            };

            fetch(`/api/device/${ip}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'success') {
                    location.reload();
                }
            });
        }

        // Fermer le modal en cliquant en dehors
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
                <tr onclick="openModal('{{ device.ip }}')" class="{% if device.is_known %}known-device{% elif device.is_new %}new-device{% endif %}">
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
            <div class="form-group">
                <label for="isKnown">Connu</label>
                <input type="checkbox" id="isKnown"> Cet appareil est connu.
            </div>
            <button class="save-button" id="saveButton">Enregistrer</button>
        </div>
    </div>
</body>
</html>
'''

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
