with

    ACCOUNT as ( select
                        cast( a.id                as VARCHAR(100) )   as acc_id_bk        ,
                        cast( a.title             as VARCHAR(25)  )   as acc_name         ,
                        ---
                        cast( a.is_archived       as VARCHAR(5)   )   as is_archived      ,
                        cast( a.created_time      as TIMESTAMP    )   as created_time     ,
                        cast( a.last_edited_time  as TIMESTAMP    )   as last_edited_time
                        ---
                 from   {{ source('01_src', 'account') }} a
                )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       --- 
from   ACCOUNT t