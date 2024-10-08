var express = require('express');
var request = require('request');
var querystring = require('querystring');
var fs = require('fs');

const app = express();
app.use(express.static(__dirname));

const client_id = process.env.CLIENT_ID;
const client_secret = process.env.CLIENT_SECRET;
const redirect_uri = process.env.REDIRECT_URI;
const PORT = process.env.PORT

var code = null;
var at = null;
var rt = null;

defineHandlingToEndpoints();
var server = app.listen(PORT, () => {
    require('child_process').exec("start "+redirect_uri+"login");
});


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

            server.close((error) => { // close web server
                if (error) {
                    console.log("Error attempting to close web server:")
                    console.log(error)
                } else {
                    console.log("Web Server Closed.")
                }
            });
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
                       else { res.redirect(redirect_uri+"success"); }
                    });

                } else { // error occurs when retrieving access token
                    console.log("Error occured while retrieving access token!")
                    console.log(error); // error.status provides error #
                    res.redirect("#" + querystring.stringify({error: "invalid_token"}));

                    server.close((error) => { // close web server
                        if (error) {
                            console.log("Error attempting to close web server:")
                            console.log(error)
                        } else {
                            console.log("Web Server Closed.")
                        }
                    });
                }
            });

        }

    });

    app.get("/success", function(req, res) { // action to take on successful token retrieval
        const data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token":at,
            "refresh_token":rt,
            "access_token_retrieved": Math.floor(Date.now() / 1000)
        };

        var jsonData = JSON.stringify(data);

        try {
            fs.writeFileSync("./data/constants.json", jsonData)
            console.log("Token Information wrote to JSON.");
            res.redirect(redirect_uri+"auth_complete.html")
        } catch (exception) {
            console.log("Failed to write token data to JSON!\n\n***")
            console.log(exception);
        }

        server.close((error) => { // close web server
            if (error) {
                console.log("Error attempting to close web server:")
                console.log(error)
            } else {
                console.log("Web Server Closed.")
            }
        });
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