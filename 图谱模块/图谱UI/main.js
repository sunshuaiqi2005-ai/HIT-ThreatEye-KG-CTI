function queryActivities() {
    const name = document.getElementById("entityInput").value;
    if (!name) {
        alert("请输入实体名称");
        return;
    }

    axios.get(`/api/activities?name=${encodeURIComponent(name)}`)
        .then(response => {
            const data = response.data;
            let output = "";

            data.forEach((item, index) => {
                output += `【行为链 ${index + 1}】\n`;

                if (item.attack_targets && item.attack_targets.length > 0) {
                    output += "攻击目标列表：\n";
                    item.attack_targets.forEach(target => {
                        output += `- ${target.name}\n`;
                    });
                } else {
                    output += "无攻击目标\n";
                }

                output += "\n";
            });

            document.getElementById("output").textContent = output;
        })
        .catch(error => {
            document.getElementById("output").textContent = "请求失败：" + error;
        });
}


function queryAttackChain() {
    const name = document.getElementById("entityInput").value;
    if (!name) {
        alert("请输入实体名称");
        return;
    }
    loadData(`/api/attack-chain?name=${encodeURIComponent(name)}`);
}

function loadData(endpoint) {
    axios.get(endpoint)
        .then(response => {
            document.getElementById("output").textContent = JSON.stringify(response.data, null, 2);
        })
        .catch(error => {
            document.getElementById("output").textContent = "请求失败：" + error;
        });
}