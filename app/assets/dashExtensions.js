window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
      function0: function (feature, latlng, context) {
        return L.circleMarker(latlng, { radius: 2 }); 
      },
      style_handle: function(feature, context) { 
        const style = context.hideout; 
        const value = feature.properties['ece_capacity'];  

        //over demand - colour red
        if (value > 1) {
                style.fillColor = '#FF0000';
        } 
        //90 - 100 demand - colour yellow
        else if (value > 0.9 && value < 1){
                style.fillColor = '#FFFF00';
        }
        //0 demand means no population - color grey
        else if (value == 0){
                style.fillColor = '#808080';
        }
        //<90 demand - colour green
        else {
                style.fillColor = '#008000';       
        }

        style.color = '#FFFFFF';
        style.weight = 1;

        return style;
    }
    },
  });