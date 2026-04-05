with

    ACCOUNT as ( select
                        cast( a.id                as VARCHAR(100) )   as account_id_bk    ,
                        cast( a.title             as VARCHAR(25)  )   as account_name     ,
                        ---
                        cast( a.is_archived       as VARCHAR(5)   )   as is_archived      ,
                        cast( a.created_time      as TIMESTAMP    )   as created_time     ,
                        cast( a.last_edited_time  as TIMESTAMP    )   as last_edited_time
                        ---
                 from   {{ source('raw', 'account') }} a
                )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       ---
from   ACCOUNT t

union all

-- System record to prevent null fact table FK
select '-1'             as account_id_bk    ,
       '-1'             as account_name     ,
       'false'          as is_archived      ,
       DATE'1990-01-01' as created_time     ,
       DATE'1990-01-01' as last_edited_time