with

    MONTH as ( select 
                      cast( m.id                as VARCHAR(100) )   as month_id_bk      ,
                      cast( m.title             as VARCHAR(12)  )   as month_name       ,
                      ---
                      cast( m.created_time      as TIMESTAMP    )   as created_time     ,
                      cast( m.last_edited_time  as TIMESTAMP    )   as last_edited_time 
                      ---
               from   {{ source('01_src', 'month') }} m
             )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select *
from MONTH t