select *
       ---
from   {{ ref('fact_transaction') }} ft
       ---
where  ft.transaction_amount is null
and    ft.transaction_status <> 'Предстои'