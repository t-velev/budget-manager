with

    YEAR as ( select
                     cast( y.id                as VARCHAR(100) )   as year_id_bk       ,
                     cast( y.title             as VARCHAR(4)   )   as year_name        ,
                     ---
                     cast( y.created_time      as TIMESTAMP    )   as created_time     ,
                     cast( y.last_edited_time  as TIMESTAMP    )   as last_edited_time
                     ---
              from   {{ source('raw', 'year') }} y
             )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       ---
from   YEAR t

union all

-- System record to prevent null fact table FK
select '-1'             as year_id_bk       ,
       '-1'             as year_name        ,
       DATE'1990-01-01' as created_time     ,
       DATE'1990-01-01' as last_edited_time