var express = require('express');
var request = require('request');
var querystring = require('querystring');
var fs = require('fs');

const app = express();
app.use(express.static(__dirname));

const client_id = "de71666388a34499a1e7e1e590e1d14d";
const client_secret = "e3d7bcc8bf9a410c85f8fec1703e9d2e";
const redirect_uri = "http://localhost:3800/";
var code = null;

var at = null;
var rt = null;

defineHandlingToEndpoints();
app.listen('3800');


function defineHandlingToEndpoints() {
    app.get('/', function(req, res) {
        res.redirect(redirect_uri+"login");
    });
    
    /// define handling for get requests to /login endpoint (for authorization)
    app.get('/login', function(req, res) {
        var state = generateRandomString(16); // recommended for security
        var scope = 'user-read-private user-read-email user-read-currently-playing';
        
        // redirect application to authorization location
        res.redirect("https://accounts.spotify.com/authorize?" + 
            querystring.stringify({
                client_id: client_id,
                response_type: "code",
                redirect_uri: redirect_uri+"callback",
                scope: scope,
                state: state
            })
        );

    });
    
    // define handling for get requests to '/callback' endpoint (access token)
    app.get("/callback", async function(req, res) {
        code = req.query.code || null;
        var state = req.query.state || null;
    
        if (state == null) {
            res.redirect("/#" + 
            querystring.stringify({
                error: "state_mismatch"
            }));
        } else {
            var authOptions = {
                url: 'https://accounts.spotify.com/api/token',
                form: {
                  code: code,
                  redirect_uri: redirect_uri+"callback",
                  grant_type: 'authorization_code'
                },
                headers: {
                  'content-type': 'application/x-www-form-urlencoded',
                  'Authorization': 'Basic ' + (new Buffer.from(client_id + ':' + client_secret).toString('base64'))
                },
                json: true
            };

            // make call to retrieve access token and refresh token
            request.post(authOptions, function(error, response, body) {

                if (!error) { // if no errors occur in process
                    at = body.access_token;
                    rt = body.refresh_token;

                    var options = {
                        url: "https://api.spotify.com/v1/me",
                        headers: { "Authorization": "Bearer " + at},
                        json: true
                    }
                    
                    // make API web call
                    request.get(options, function(error, response, body) {
                       if (error) { console.log("Error retrieving access token!"); }
                    });

                    res.redirect(redirect_uri+"success");

                } else { // error occurs when retrieving access token
                    console.log("Error occured while retrieving access token!")
                    console.log(error); // error.status provides error #
                    res.redirect("#" + querystring.stringify({error: "invalid_token"}));
                }
            });

        }

    });

    app.get("/success", function(req, res) { // action to take on successful token retrieval
        populateJSON(at);
        
    });
}

/**
 * 
 * @return a refresh token that can be used to continue retrieving data after access token expiration 
 */
function getRefreshToken() {}

/**
 * Populates a JSON file with necessary display information regarding the currently playing song
 * @param {*} info JSON data containing all Spotify song information from an API request. This 
 * must include the user-read-currently-playing scope 
 */
function populateJSON(info) {
    var options = {
        url: "https://api.spotify.com/v1/me/player/currently-playing",
        headers: { "Authorization": "Bearer " + at},
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
      

    });
}

function generateRandomString(length) {
    const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"

    var num = 0;
    var rand = "";

    for (var i=0;i<length;i++) {
        num = Math.floor(Math.random()*(possible.length-1));
        rand += possible.charAt(num);
    }

    return rand;
}