with

    BUDGET as ( select
                       cast( b.id                as VARCHAR(100)  )   as budget_id_bk     ,
                       cast( b.title             as VARCHAR(50)   )   as budget_name      ,
                       ---
                       cast( b.year_id           as VARCHAR(100)  )   as year_id          ,
                       cast( y.title             as VARCHAR(100)  )   as year_name        ,
                       ---
                       cast( b.month_id          as VARCHAR(100)  )   as month_id         ,
                       cast( m.title             as VARCHAR(100)  )   as month_name       ,
                       ---
                       cast( b.category_id       as VARCHAR(100)  )   as category_id      ,
                       cast( c.title             as VARCHAR(100)  )   as category_name    ,
                       ---
                       cast( b.subcategory_id    as VARCHAR(100)  )   as subcategory_id   ,
                       cast( s.title             as VARCHAR(100)  )   as subcategory_name ,
                       ---
                       cast( b.budget_amnt       as NUMERIC(27,2) )   as budget_amnt      ,
                       ---
                       cast( b.is_archived       as VARCHAR(5)    )   as is_archived      ,
                       cast( b.created_time      as TIMESTAMP     )   as created_time     ,
                       cast( b.last_edited_time  as TIMESTAMP     )   as last_edited_time
                       ---
                from   {{ source("01_src", "budget") }} b
                       ---
                       LEFT join {{ source("01_src", "year"       ) }} y on ( y.id = b.year_id        )
                       LEFT join {{ source("01_src", "month"      ) }} m on ( m.id = b.month_id       )
                       LEFT join {{ source("01_src", "category"   ) }} c on ( c.id = b.category_id    )
                       LEFT join {{ source("01_src", "subcategory") }} s on ( s.id = b.subcategory_id )
              )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.budget_id_bk     ,
       t.budget_name      ,
       t.year_name        ,
       t.month_name       ,
       t.category_name    ,
       t.subcategory_name ,
       t.budget_amnt      ,
       t.is_archived      ,
       t.created_time     ,
       t.last_edited_time
       ---
from   BUDGET t

