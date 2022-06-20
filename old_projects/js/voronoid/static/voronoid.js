/******************************************************************************
 * Voronoid.js
 *
 * Adam Scherlis
 * Fall 2010
 *
 * A colorful Voronoi game with neighbor-based clustering bonuses, using
 * Processing.JS and Raymond Hill's Voronoi library for Javascript.
 *****************************************************************************/

// Main program function, attached to canvas with Processing API
function sketchProc(p) {
    
    // Global constants for total players and rounds
    var PLAYERS;
    var MINP = 2;
    var MAXP = 6;
    
    var ROUNDS;
    var MINR = 1;
    var MAXR = 20;

    // Hues for each player (up to 6 total)
    var PCOLORS = [0, 240, 120, 60, 180, 300];

    // Set color mode
    p.colorMode(p.HSB, 360, 100, 100);

    // Game state
    var state = "start";

    // Variables for current round and player
    var player = 0;
    var round = 0;

    var scores = [];
    var winner;

    // Marker class: each has an owner, a location, and size/neighbor data
    function Marker(x,y,o) {
        this.x = x;
        this.y = y;
        this.owner = o;
        this.score = 0;
        this.neighbors = 0;
    };

    // Array of markers
    var markers = [];
    
    // set up canvas
    p.size(800,600);
    p.background(0);
    
    // Begin game (called by PLAY button)
    p.startGame = function() {
        // Temporary variable for the HTML form
        var iform = document.forms[0];

        // Get number of players and rounds from the form values
        PLAYERS = iform.elements["players"].value;
        ROUNDS = iform.elements["rounds"].value;
        
        // Error checking: make sure everything exists and is within bounds
        if (MINR <= ROUNDS && ROUNDS <= MAXR && MINP <= PLAYERS && PLAYERS <= MAXP) { 
            
            // Change game state and update page
            state = "play";
            updateScore();
            updateCount();
            updateCursor();

            // Hide #intro (and show #game, behind it)
            document.getElementById("intro").style.display = "none";
        }
    }

    // Global variables for rhill's voronoi library
    var voronoi = new Voronoi();
    var diagram;
    var bbox = {xl:0, xr:p.width, yt:0, yb:p.height};
    
    // Create Processing draw() function
    p.draw = function() {};

    // Mouse-click handler
    p.mouseClicked = function() {
        // store mouse location
        var x = p.mouseX;
        var y = p.mouseY;

        // if game state is "play", place a new marker
        switch (state) {
            case "start": break;
            case "play": placeMarker(x,y); break;
            case "end": break;
        }
    };

    function placeMarker(x,y) {
        // Check for duplicates
        for (i in markers) {
            // Multiple markers on the same site breaks Voronoi library
            if (markers[i].x == x && markers[i].y == y) {
                return;
            }
        }

        // Create new marker
        var newmark = new Marker(x, y, player);
        // Add marker to list
        markers.push(newmark);

        // Render Voronoi diagram
        updateScreen();
        
        // Update player and round info
        player++;
        if (player >= PLAYERS) {
            player = 0;
            round++;
            
            // Set game state to end if last round has ended
            if (round >= ROUNDS) {
                state = "end";

                // Create temporary variable for highest score
                var max = 0;

                // Reset winner to 0
                winner = 0;

                // Update everything one last time
                updateScore();
                updateCount();
                updateCursor();

                // Calculate winner by looping through players
                for (var i = 0; i < PLAYERS; i++) {
                    if (scores[i] > max) {
                        max = scores[i];
                        winner = i;
                    }
                }
            }
        }
        
        // Update cursor
        updateCursor();
        // Update scores
        updateScore();
        // Update text counter
        updateCount();
    }
    
    // Update the section displaying score information
    function updateScore() {
        
        // Reset all scores
        for (var i = 0; i < PLAYERS; i++) {
            scores[i] = 0;
        }
        
        // Create variable for new innerHTML
        var newhtml = "";
    
        // Create variable for total score of all players
        var total = 0;

        // Add up all scores
        for (i in markers) {
            // Add marker score to player score
            scores[markers[i].owner] += markers[i].score;

            // Add marker score to total score
            total += markers[i].score;
        }

        // Don't divide by zero! (everyone starts with 0% out of 100%)
        if (total == 0) {total = 1;}

        // Calculate each player's score and generate the HTML for it
        for (var i = 0; i < PLAYERS; i++) {
            // Scale player score to a percentage
            scores[i] = 100 * scores[i] / total;
            
            // This div will be a .pscore (see style.css)
            var classes = "pscore ";
            if (i == player && state == "play") {
                // If it's the current player, it's a .cscore
                classes += "cscore ";
            } else if (i == winner && state == "end") {
                // If it's the winner, it's a .wscore
                classes += "wscore ";
            }

            // Create basic skeleton of div
            newhtml += "<div class=\""+classes+"\" style=\"left:"+80*i+"px;\">";
            // Display the appropriate cursor image in the cell
            newhtml += "<img src=\"cursors/cursor"+i+".png\"></img>";
            // Display the score
            newhtml += Math.round(scores[i])+"%";
            // End div
            newhtml += "</div>";
        }

        // Update #score with new HTML
        document.getElementById("score").innerHTML = newhtml;
    }

    // Update text counters
    function updateCount() {
        // Current player should be player N at end of game
        var p = (state == "end") ? PLAYERS : player+1;
        // Round should be final round at end of game
        var r = (state == "end") ? ROUNDS : round+1;

        // Button changes text at end of game
        var btext = (state == "end") ? "Play Again!" : "Restart";

        // Create variable for new HTML
        var newhtml = "";
        // Create button
        newhtml += "<button type\"button\" onClick=\"history.go(0)\">"+btext+"</button>&nbsp;&nbsp;&nbsp;&nbsp;";
        // Create player counter
        newhtml += p + "/" + PLAYERS + "&nbsp;&nbsp;&nbsp;&nbsp;";
        // Round counter
        newhtml += r + "/" + ROUNDS;
        
        // Update #count with new html
        document.getElementById("count").innerHTML = newhtml;
    }

    // Update cursor
    function updateCursor() {
        // If play is under way, change cursor to match current player. Otherwise, no new cursor.
        var newhtml = (state == "play") ? "body {cursor: url(cursors/cursor"+player+".png),default;}" : "";

        // Update cursor with HTML, which contains CSS to change the cursor (on Windows/Linux)
        document.getElementById("cursor").innerHTML = newhtml;
    }
    
    // Render Voronoi diagram based on Markers, using rhill's library
    function updateScreen() {
        // Compute Voronoi diagram
        voronoi.setSites(markers);
        diagram = voronoi.compute(bbox);
        // Sites list corresponds to markers list (sites[0] matches markers[0], etc)
        var sites = voronoi.getSites();
        var cells = diagram.cells;
        var edges = diagram.edges;
        
        p.stroke(0);
        
        // Reset neighbors to 0
        for (i in markers) {
            markers[i].neighbors = 0;
        }

        // Calculate neighbors with edge.lSite/rSite
        for (i in edges) {
            edge = edges[i];
            if (edge.rSite) {
                var li = 0;
                var ri = 0;

                // Loop through sites to identify position in list
                for (i in sites) {
                    if (sites[i].id == edge.lSite.id) {
                        li = i;
                    } else if (sites[i].id == edge.rSite.id) {
                        ri = i;
                    }
                }

                // If both sides are the same, add a neighbor for each.
                if (markers[li].owner == markers[ri].owner) {
                    markers[li].neighbors++;
                    markers[ri].neighbors++;
                }
            }
        }
        
        // Draw each cell
        // Loop through sites/markers
        for (i in sites) {
            // Get current site
            var site = sites[i];
            var marker = markers[i];
            // Cells are indexed by ID of corresponding site (see rhill-voronoi)
            var cell = cells[site.id];
            var color = PCOLORS[marker.owner];
            
            // Calculate brightness
            var bright = 30 + 14*markers[i].neighbors;
            
            // Set player color
            p.fill(color, 100, bright);
            
            var area = 0;

            if (cell) {
                // Begin Processing.js shape
                p.beginShape();
                
                halfedges = cell.halfedges;
                
                // Get first point and create variables
                var prev = halfedges[0].getStartpoint();
                var next;

                for (j in halfedges) {
                    // Get next point
                    next = halfedges[j].getEndpoint();

                    // Add vertex to Processing shape
                    p.vertex(next.x, next.y);

                    // Add next term to area total
                    // FORMULA: 1/2 |x1y2 - x2y1 + x2y3 - x3y2 ...|
                    // See http://mathworld.wolfram.com/PolygonArea.html
                    area += prev.x * next.y - next.x * prev.y;
                    prev = next;
                }
                
                // Divide area by two (see formula)
                area = Math.abs(area/2);
                marker.score = area * (1 + 0.5*marker.neighbors);

                // Finish Processing shape
                p.endShape(p.CLOSE);
            } else {
                // First marker doesn't create a cell, so just use rect() to render...
                p.rect(0,0,p.width,p.height);

                // ...And width*height to get area
                marker.score = p.width * p.height;
            }

            // Set fill color to black
            p.fill(0);

            // Add dot to show marker
            p.ellipse(marker.x,marker.y,5,5);
        }
    }
}

// Get canvas element
var canvas = document.getElementById("canvas");
// Attach code to canvas and create a Processing instance
var processing = new Processing(canvas, sketchProc);
