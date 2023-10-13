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
                style.fillColor = '#FFA500';
        }
        //-1 demand means no population - color dark grey
        else if (value == -1){
                style.fillColor = '#000000';
        }
        //<90 demand - colour green
        else {
                style.fillColor = '#008000';       
        }

        style.weight = 1;

        return style;
    },

    ta_filter: function(feature, context) {

        const over = context.hideout['over'];
        const selected = context.hideout['ta'];
        const view = context.hideout['view']

        const poly_ta = feature.properties['ta'];
        const demand = feature.properties['ece_capacity']

       

        if (over == "True"){
                if(demand > 0.9){
                        return true
                }
        } 

        if (poly_ta == selected){
                return true
        } else {
                return false
        }
        

        
    },
       
    marker_filter: function(feature, context){
       
        const view = context.hideout['view'];

        if (view == "address"){
                const lat1 = context.hideout['lat']
                const lng1 = context.hideout['lng']
                const dist = context.hideout['dist']

                const lat2 = feature.properties['Latitude']
                const lng2 = feature.properties['Longitude']

                

                // Radius of the Earth in kilometers
                const earthRadius = 6371; // Use 3959 for miles
        
                // Convert latitude and longitude from degrees to radians
                const lat1Rad = (lat1 * Math.PI) / 180;
                const lng1Rad = (lng1 * Math.PI) / 180;
                const lat2Rad = (lat2 * Math.PI) / 180;
                const lng2Rad = (lng2 * Math.PI) / 180;
        
                // Haversine formula
                const dLat = lat2Rad - lat1Rad;
                const dLon = lng2Rad - lng1Rad;
        
                const a =
                Math.sin(dLat / 2) ** 2 +
                Math.cos(lat1Rad) * Math.cos(lat2Rad) * Math.sin(dLon / 2) ** 2;
        
                const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        
                // Calculate the distance
                const distance = earthRadius * c;

                if (distance <= dist){
                        return true;
                } else {
                        return false;
                }
        }

        const show = context.hideout['show'];

        if (show == "False"){
                return false
        }


        if (view == "ta"){
                const selected = context.hideout['ta'];
                const marker_ta = feature.properties['Territorial Authority'];

                if (marker_ta == selected){
                        return true
                } else {
                        return false
                }
        }

        return false 
    }
    },
  });