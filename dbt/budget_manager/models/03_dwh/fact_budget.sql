with

    BUDGET as ( select
                            sb.budget_id_bk       ,
                            sb.budget_name        ,
                            ---
                            sb.period_end         ,
                            sb.budget_amount      ,
                            ---
                            sb.year_id            ,
                            sb.month_id           ,
                            sb.category_id        ,
                            sb.subcategory_id     ,
                            ---
                            sb.is_archived        ,
                            sb.created_time       ,
                            sb.last_edited_time
                            ---
                     from   {{ ref('stg_budget') }} sb
                    ) ,

    CATEGORY    as ( select
                            dc.category_id_bk     ,
                            dc.category_name      ,
                            ---
                            dc.category_type      ,
                            ---
                            dc.is_archived        ,
                            dc.created_time       ,
                            dc.last_edited_time   ,
                            ---
                            dc.dk                 ,
                            dc.scd2_valid_from    ,
                            dc.scd2_valid_to
                            ---
                     from   {{ ref('dim_category') }} dc
                    ) ,

    SUBCATEGORY as ( select
                            ds.subcategory_id_bk  ,
                            ds.subcategory_name   ,
                            ---
                            ds.subcategory_type   , -- [Приход, Разход]
                            ds.priority           , -- [Плаваща, Фиксирана, null]
                            ds.due_date           ,
                            ---
                            ds.is_archived        ,
                            ds.created_time       ,
                            ds.last_edited_time   ,
                            ---
                            ds.dk                 ,
                            ds.scd2_valid_from    ,
                            ds.scd2_valid_to
                            ---
                     from   {{ ref('dim_subcategory') }} ds
                    ) ,

    YEAR        as ( select
                            dy.year_id_bk         ,
                            dy.year_name          ,
                            ---
                            dy.created_time       ,
                            dy.last_edited_time   ,
                            ---
                            dy.dk                 ,
                            dy.scd2_valid_from    ,
                            dy.scd2_valid_to
                            ---
                     from   {{ ref('dim_year') }} dy
                    ) ,

    MONTH       as ( select
                            dm.month_id_bk        ,
                            dm.month_name         ,
                            ---
                            dm.created_time       ,
                            dm.last_edited_time   ,
                            ---
                            dm.dk                 ,
                            dm.scd2_valid_from    ,
                            dm.scd2_valid_to
                            ---
                     from   {{ ref('dim_month') }} dm
                    )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.budget_id_bk         as budget_id_bk   ,
       ---
       t.budget_name          as budget_name    ,
       ---
       t.period_end           as period_end     ,
       ---
       t.budget_amount        as budget_amount  ,
       ---
       coalesce(c.dk, (select dk from CATEGORY    where category_id_bk    = '-1'))   as category_dk    ,  -- dbt sets dk to a hash value by default. I have to use a subquery to find the dk.
       coalesce(s.dk, (select dk from SUBCATEGORY where subcategory_id_bk = '-1'))   as subcategory_dk ,  -- If a null or bad value for *_id_bk appears, create_drop_costraints.sql
       coalesce(y.dk, (select dk from YEAR        where year_id_bk        = '-1'))   as year_dk        ,  -- won't be able to create the foreign key. It will fail with error like:
       coalesce(m.dk, (select dk from MONTH       where month_id_bk       = '-1'))   as month_dk          -- 'Key (month_dk)=(-1) is not present in table "dim_month"'
       ---
       ---
from   BUDGET t
       ---
       LEFT join CATEGORY    /* with */ c on ( c.category_id_bk     = t.category_id     and
                                               c.scd2_valid_from   <= t.period_end      and
                                               c.scd2_valid_to      > t.period_end
                                              )

       LEFT join SUBCATEGORY /* with */ s on ( s.subcategory_id_bk  = t.subcategory_id  and
                                               c.scd2_valid_from   <= t.period_end      and
                                               c.scd2_valid_to      > t.period_end
                                              )

       LEFT join YEAR        /* with */ y on ( y.year_id_bk         = t.year_id         and
                                               y.scd2_valid_from   <= t.period_end      and
                                               y.scd2_valid_to      > t.period_end
                                              )

       LEFT join MONTH       /* with */ m on ( m.month_id_bk        = t.month_id        and
                                               m.scd2_valid_from   <= t.period_end      and
                                               m.scd2_valid_to      > t.period_end
                                              )
