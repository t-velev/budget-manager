with

    MONTH as ( select
                      cast( m.id                as VARCHAR(100) )   as month_id_bk      ,
                      cast( m.title             as VARCHAR(12)  )   as month_name       ,
                      ---
                      cast( m.created_time      as TIMESTAMP    )   as created_time     ,
                      cast( m.last_edited_time  as TIMESTAMP    )   as last_edited_time
                      ---
               from   {{ source('raw', 'month') }} m
             )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       ---
from   MONTH t

union all

-- System record to prevent null fact table FK
select '-1'             as month_id_bk      ,
       '-1'             as month_name       ,
       DATE'1990-01-01' as created_time     ,
       DATE'1990-01-01' as last_edited_time