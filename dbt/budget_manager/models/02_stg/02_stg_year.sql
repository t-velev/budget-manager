with

    YEAR as ( select 
                     cast( y.id                as VARCHAR(100) )   as year_id_bk       ,
                     cast( y.title             as VARCHAR(4)   )   as year_name        ,
                     ---
                     cast( y.created_time      as TIMESTAMP    )   as created_time     ,
                     cast( y.last_edited_time  as TIMESTAMP    )   as last_edited_time 
                     ---
              from   {{ source('01_src', 'year') }} y
             )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select *
from YEAR t