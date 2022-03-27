// console.log("test")
// addElement()
document.body.onload = addElement()

function addElement ()
{
    data = [{"game_id": "Game 1", "sports_title": "NCAAB", "commence_time": "2022-01-29T19:05:40Z",
         "home_team": "Arkansas Razorbacks", "away_team": "West Virginia Mountaineers", "market": "h2h", "edge": 13.22,
          "home_team_lines": [{"team": "Arkansas Razorbacks", "last_update": "2022-01-29T21:06:53Z", "price": -500, "bookie": "MyBookie.ag"}],
           "away_team_lines": [{"team": "West Virginia Mountaineers", "last_update": "2022-01-29T21:06:55Z", "price": 2800, "bookie": "William Hill (US)"}]}, {"game_id": "Game 2"}, {"game_id": "Game 3"}, {"game_id": "Game 4"}]
    // serverRequest('arbs.json')
    appendData(data)
}

function serverRequest(jsonName)
{
    fetch('arbs.json')
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                appendData(data);
            })
            .catch(function (err) {
                console.log('error: ' + err);
            });
}

function appendData(data)
{
    var mainContainer = document.getElementById("myData");
    for (var i = 0; i < data.length; i++) {
        var div = document.createElement("div");
        div.id = "box"
        div.innerHTML = 'game_id: ' + data[i].game_id;
        var head = document.createElement("hr")
        head.id = "breaker"
        div.append(head)
        mainContainer.append(div);
    }
}