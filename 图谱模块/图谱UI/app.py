
from flask import Flask, render_template, request, jsonify
from utils import create_graph_connection, find_activities, analyze_attack_chain, analyze_attacker, analyze_locations

app = Flask(__name__)
graph = create_graph_connection()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/activities")
def api_activities():
   
    try:
        name = request.args.get("name", "")
        records = find_activities(graph, name)
        data = []
        for rec in records:
            
            rels = rec.get("attack_relations", [])
            targets = rec.get("attack_targets", [])
            rel_info = []
            for rel in rels:
                print(rel)
                try:
                    rel_info.append({
                        "type": rel["type"],
                        "threat_score": rel["threat_score"]
                    })
                except:
                    rel_info.append({})

            target_info = []
            for node in targets:
                target_info.append({"name": node})

            data.append({
                "attack_relations": rel_info,
                "attack_targets": target_info
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/attack-chain")
def api_attack_chain():
    try:
        name = request.args.get("name", "")
        records = analyze_attack_chain(graph, name)
        print(records)
        data = []
        for rec in records:
            nodes = rec.get("chain_nodes", [])
            node_names = [n.get("name", "未知") for n in nodes if hasattr(n, "get")]
            path_str = " → ".join(node_names)
            score = rec.get("weighted_threat_score", 0)
            data.append({
                "path": path_str,
                "score": round(score, 2)
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/attacker-network")
def api_attacker_network():
    try:
        query = """
        MATCH (s)-[r]->(t)
        WHERE s.name IS NOT NULL AND t.name IS NOT NULL
        RETURN s.name AS source, t.name AS target
        LIMIT 100
        """
        data = []
        for record in graph.run(query):
            data.append({
                "source": record["source"],
                "target": record["target"]
            })
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/geo-map")
def api_geo_map():
    try:
        records = analyze_locations(graph)
        data = []
        for rec in records:
            data.append({
                "threat": rec["threats"]["name"],
                "location": rec["locations"]["name"]
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
