$(document).ready(function() {	
	
    /**
     * store the value of and then remove the title attributes from the
     * abbreviations (thus removing the default tooltip functionality of
           * the abbreviations)
     */
    $('abbr').each(function(){		
      
      $(this).data('title',$(this).attr('title'));
      $(this).removeAttr('title');
    
    });

     
  
    /**
     * when abbreviations are clicked trigger their mouseover event then fade the tooltip
     * (this is friendly to touch interfaces)
     */
    $('abbr').click(function(){
      
      $(this).mouseover();
      
      // after a slight 2 second fade, fade out the tooltip for 1 second
      $(this).next().animate({opacity: 0.9},{duration: 1000, complete: function(){
        $(this).fadeOut(1000);
      }});
      
    });
    
    /**
     * Remove the tooltip on abbreviation mouseout
     */
    $('abbr').mouseout(function(){
        
      $(this).next('.tooltip').remove();				

    });	
    
  });