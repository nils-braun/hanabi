function valueToColor(value) {
    if(value == 0) {
        return "green";
    } else if (value == 1) {
        return "blue";
    } else if (value == 2) {
        return "white";
    } else if (value == 3) {
        return "red";
    }else if (value == 4) {
        return "yellow";
    } else {
        throw "Invalid color";
    }
}

function valueToColorChar(value) {
    if(value == 0) {
        return "green";
    } else if (value == 1) {
        return "blue";
    } else if (value == 2) {
        return "white";
    } else if (value == 3) {
        return "red";
    }else if (value == 4) {
        return "yellow";
    } else {
        throw "Invalid color";
    }
}

function addBindings() {
    $(".circles").each(function(index, circleParent) {
        var numberOfOnCircles = $(circleParent).attr("data-on");
        var numberOfTotalCircles = $(circleParent).attr("data-total");

        for(var circleCounter = 0; circleCounter < numberOfTotalCircles; circleCounter++) {
            var classes = "circle-inner ";
            if(circleCounter < numberOfOnCircles) {
                classes += "circle-on";
            } else {
                classes += "circle-off";
            }
            $(circleParent).append("<span class='" + classes + "'></span>")
        }
    });

    $(".card").each(function(index, cardObject) {
        var card = $(cardObject);

        var cardValue = card.attr("data-card-value");
        var cardColor = card.attr("data-card-color");

        if(cardValue != -1 || cardColor != -1) {
            card.addClass("card-back");

            if(cardValue != -1) {
                card.append("<span class='card-value card-text'>" + cardValue + "</span>");
            }

            if(cardColor != -1) {
                card.addClass("card-color-" + cardColor);
                card.append("<span class='card-color card-text'>" + cardColor + "</span>");
            }
        }
    }).on("click", function() {
        $(".card-turn").hide();
        $(this).children(".card-turn").show();
    }).mouseleave(function() {
        $(this).children(".card-turn").hide();
    });

    $(".card-turn").hide().mouseenter(function() {
        var turn_id = this.className.split(/\s+/).filter(function(x) { return x.startsWith("card-turn-"); });
        $("." + turn_id).parent().addClass("selected");
    }).mouseleave(function() {
        $(".card").removeClass("selected");
    });
}

$(document).ready(function() {
    addBindings();
});
