var express = require('express');
var request = require('request');
var fs = require("fs");

var token = null;
var refresh = null;

// get at and rt values
data = JSON.parse(fs.readFileSync("./constants.json"));

token = data.access_token;
refresh = data.refresh_token;

// if token is within fifteen seconds of expiring, request a new one
if (3600 - (Math.floor(Date.now() / 1000) - data.access_token_retrieved) <= 15) { // change to 15 after confirmed working
    
    var client_id = data.client_id;
    var client_secret = data.client_secret;

    var authOptions = {
        url: 'https://accounts.spotify.com/api/token',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + (new Buffer.from(client_id + ':' + client_secret).toString('base64'))
        },
        form: {
            grant_type: 'refresh_token',
            refresh_token: refresh
        },
        json: true
    };

    request.post(authOptions, function(error, response, body) {
        if (!error && response.statusCode == 200) {

            token = body.access_token; // update access token
            if (body.refresh_token != null) { // check for new refresh token
                refresh = body.refresh_token;
            }

            // write updated constants values to json file
            const updatedData = {
                "access_token": token,
                "refresh_token": refresh,
                "access_token_retrieved": Math.floor(Date.now() / 1000),
                "client_id": client_id,
                "client_secret": client_secret
            }

            var jsonData = JSON.stringify(updatedData);

            try {
                fs.writeFileSync("./constants.json", jsonData);
                console.log("Successfully generated new access token!");
            } catch(exception) {
                console.log("Failed to write token data to JSON!\n\n***")
                console.log(exception);                            
            }
        } else { // error case
            console.log("Failed to retrieve refreshed access token.");
            console.log(error);

        }
    });

}



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
            console.log("**********");
            console.log(body);
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
                "progress": body.progress_ms,
                "dur": body.item.duration_ms,
                "url":body.item.preview_url // replace w/ 30sec preview to test
            };
        
            var jsonData = JSON.stringify(data); // create JSON format data        
        }
        
        try {
            fs.writeFileSync("./data.json", jsonData)
        } catch (exception) {
            console.log("Failed to write data to JSON file!\n\n***")
            console.log(exception);
        }

    });

} else {
    console.log("Access or Refresh token was null.")
}