with

    BUDGET as ( select
                       cast( b.id                as VARCHAR(100)  )   as budget_id_bk      ,
                       cast( b.title             as VARCHAR(50)   )   as budget_name       ,
                       ---
                       cast( b.period_end        as DATE          )   as period_end        ,
                       ---
                       cast( b.year_id           as VARCHAR(100)  )   as year_id           ,
                       cast( b.month_id          as VARCHAR(100)  )   as month_id          ,
                       ---
                       cast( s.category_id       as VARCHAR(100)  )   as category_id       ,
                       ---
                       cast( b.subcategory_id    as VARCHAR(100)  )   as subcategory_id    ,
                       ---
                       cast( b.budget_amount     as NUMERIC(27,2) )   as budget_amount     ,
                       ---
                       cast( b.is_archived       as VARCHAR(5)    )   as is_archived       ,
                       cast( b.created_time      as TIMESTAMP     )   as created_time      ,
                       cast( b.last_edited_time  as TIMESTAMP     )   as last_edited_time
                       ---
                from   {{ source('raw', 'budget') }} b
                       ---
                       LEFT join {{ source('raw', 'subcategory') }} s on (s.id = b.subcategory_id)
              )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       --- 
from   BUDGET t

