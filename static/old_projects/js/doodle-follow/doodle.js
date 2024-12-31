// fill viewport
var canv = document.getElementById( 'canvas' );
canv.width = window.innerWidth;
canv.height = window.innerHeight;

var width = canv.width;
var height = canv.height;
var x = width / 2.0;
var y = height / 2.0;
var t = 0.0;

var STEP = 1.0;
var CURVE = 0.4;
var DELAY = 0.0; // ms

var ctx = canv.getContext( '2d' );

var mousex = x;
var mousey = y;

ctx.strokeRect( 0, 0, width, height );

function draw()
{
    ctx.beginPath();
    ctx.moveTo( x, y );

    var oldx = x, oldy = y;

    x += STEP * Math.cos( t );
    y += STEP * Math.sin( t );

    var dt = getcurve(oldx,oldy);

    t += dt;
    
    check();

    ctx.lineTo( x, y );

    ctx.stroke();
}

function getcurve(ox,oy)
{
    var rand = Math.random();

    // cross product of direction vector and vector to mouse
    var cross = (x-ox)*(mousey-y) - (y-oy)*(mousex-x);

    if (cross > 0)
    {
        if (rand > 0.75)
            return -CURVE;
        else if (rand > 0.50)
            return 0;
        else
            return CURVE;
    }
    else
    {
        if (rand > 0.50)
            return -CURVE;
        else if (rand > 0.25)
            return 0;
        else
            return CURVE;
    }
}

function check()
{
    if ( y > height - 1 )
    {
        y = 0;
        ctx.moveTo( x, y );
    }
    else if ( y < 0 )
    {
        y = height - 1;
        ctx.moveTo( x, y );
    }

    if ( x > width - 1 )
    {
        x = 0;
        ctx.moveTo( x, y );
    }
    else if ( x < 0 )
    {
        x = width - 1;
        ctx.moveTo( x, y );
    }
}

function getmouse(event)
{
    mousex = event.clientX;
    mousey = event.clientY;
}

window.setInterval( draw, DELAY );
