var request = require('request');
var fs = require("fs");

var token = null;
var refresh = null;

// get at and rt values
data = JSON.parse(fs.readFileSync("./constants.json"));

token = data.access_token;
refresh = data.refresh_token;

if (token != null && refresh != null) {

    var options = {
        url: "https://api.spotify.com/v1/me/player/currently-playing",
        headers: { "Authorization": "Bearer " + token},
        json: true
    }

    // make API web call
    request.get(options, function(error, response, body) {
        if (error) {
            console.log("Error retrieving data!");
            return null;
        } else {
            var artists = "";
            for (var i = 0; i<body.item.artists.length; i++ ) {
                artists += body.item.artists[i].name;
                if (i+1 != body.item.artists.length) {
                    artists += ", ";
                }
            }
        
            const data = {
                "name":body.item.name,
                "artists": artists,
                "album": body.item.album.name,
                "album_cov": body.item.album.images[2].url,
                "album_release": body.item.album.release_date,
                "progress": Math.floor(body.progress_ms / 1000),
                "dur": Math.floor(body.item.duration_ms / 1000)
            };
        
            var jsonData = JSON.stringify(data); // create JSON format data
            
            console.log(jsonData);
        
        }
        
        try {
            fs.writeFileSync("./data.json", jsonData)
            console.log("Successfully wrote data to JSON!");
        } catch (exception) {
            console.log("Failed to write data to JSON file!\n\n***")
            console.log(exception);
        }

    });

} else {
    console.log("Access or Refresh token was null. Terminating program.")

}