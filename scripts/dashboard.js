// Lógica de dashboard: transações, objetivos, metas, gráficos
// Persistência: localStorage com chaves:
// - numus_transactions (array)
// - numus_objective (string)
// - numus_goals (array)

(function(){
    // ---------- helpers ----------
    function moneyFmt(v){
        return 'R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2});
    }
    function parseDateIso(d){
        // aceita YYYY-MM-DD ou Date
        if (!d) return '';
        if (d instanceof Date) return d;
        return new Date(d);
    }
    function monthKey(date){
        const d = parseDateIso(date);
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
    }

    // ---------- storage ----------
    const STORAGE = {
        txKey: 'numus_transactions',
        objKey: 'numus_objective',
        goalsKey: 'numus_goals'
    };

    function loadTransactions(){
        try {
            return JSON.parse(localStorage.getItem(STORAGE.txKey) || '[]');
        } catch(e) { return []; }
    }
    function saveTransactions(tx){
        localStorage.setItem(STORAGE.txKey, JSON.stringify(tx));
    }
    function loadObjective(){
        return localStorage.getItem(STORAGE.objKey) || '';
    }
    function saveObjective(s){
        localStorage.setItem(STORAGE.objKey, s);
    }
    function loadGoals(){
        try {
            return JSON.parse(localStorage.getItem(STORAGE.goalsKey) || '[]');
        } catch(e){ return []; }
    }
    function saveGoals(g){
        localStorage.setItem(STORAGE.goalsKey, JSON.stringify(g));
    }

    // ---------- demo data inicial (apenas se array vazio) ----------
    if (!localStorage.getItem(STORAGE.txKey)){
        const demo = [
            // type: income | expense | invest
            {id:1, date: '2025-01-05', description: 'Salário', category: 'Salário', type: 'income', amount: 3000},
            {id:2, date: '2025-01-12', description: 'Aluguel', category: 'Moradia', type: 'expense', amount: 900},
            {id:3, date: '2025-01-20', description: 'Transporte', category: 'Transporte', type: 'expense', amount: 120},
            {id:4, date: '2025-02-03', description: 'Freelance', category: 'Freelance', type: 'income', amount: 500},
            {id:5, date: '2025-02-15', description: 'Compra investimentos - Viagem', category: 'Meta:Viagem', type: 'invest', amount: 200},
            {id:6, date: '2025-03-10', description: 'Supermercado', category: 'Alimentação', type: 'expense', amount: 350},
            {id:7, date: '2025-03-20', description: 'Investimento Mensal', category: 'Investimentos', type: 'invest', amount: 300}
        ];
        saveTransactions(demo);
    }

    // ---------- DOM refs ----------
    const elTotalSaldo = document.getElementById('total-saldo');
    const elTotalEntradas = document.getElementById('total-entradas');
    const elTotalSaidas = document.getElementById('total-saidas');
    const elTotalInvestimentos = document.getElementById('total-investimentos');

    const transactionsTableBody = document.querySelector('#transactions-table tbody');

    // objective elements
    const objectiveDisplay = document.getElementById('objective-display');
    const objectiveInput = document.getElementById('objective-input');
    const editObjectiveBtn = document.getElementById('edit-objective');

    // goals modal/list
    const addGoalBtn = document.getElementById('add-goal');
    const goalModal = document.getElementById('goal-modal');
    const goalNameInput = document.getElementById('goal-name');
    const goalTargetInput = document.getElementById('goal-target');
    const goalCategoryInput = document.getElementById('goal-category');
    const saveGoalBtn = document.getElementById('save-goal');
    const cancelGoalBtn = document.getElementById('cancel-goal');
    const goalsListEl = document.getElementById('goals-list');

    // charts
    const pieCanvas = document.getElementById('pieChart');
    const lineCanvas = document.getElementById('lineChart');
    let pieChart, lineChart;

    // ---------- UI / lógica ----------
    function computeTotals(transactions){
        let income = 0, expense = 0, invest = 0;
        transactions.forEach(t => {
            if (t.type === 'income') income += Number(t.amount);
            else if (t.type === 'expense') expense += Number(t.amount);
            else if (t.type === 'invest') invest += Number(t.amount);
        });
        const saldo = income - expense;
        return {income, expense, invest, saldo};
    }

    function renderTotals(){
        const tx = loadTransactions();
        const totals = computeTotals(tx);
        elTotalEntradas.textContent = moneyFmt(totals.income);
        elTotalSaidas.textContent = moneyFmt(totals.expense);
        elTotalInvestimentos.textContent = moneyFmt(totals.invest);
        elTotalSaldo.textContent = moneyFmt(totals.saldo);
    }

    function renderTransactionsTable(limit = 7){
        const tx = loadTransactions().slice().sort((a,b)=> new Date(b.date)-new Date(a.date));
        transactionsTableBody.innerHTML = '';
        tx.slice(0,limit).forEach(t=>{
            const tr = document.createElement('tr');
            const d = new Date(t.date);
            tr.innerHTML = `<td>${d.toLocaleDateString('pt-BR')}</td>
                            <td>${t.description}</td>
                            <td>${t.category}</td>
                            <td class="${t.type==='expense'?'text-red': t.type==='invest'?'text-yellow':'text-green'}">${moneyFmt(Number(t.amount))}</td>`;
            transactionsTableBody.appendChild(tr);
        });
    }

    function updatePieChart(){
        const tx = loadTransactions();
        // agrupar apenas despesas (ou incluir investimentos se quiser)
        const byCat = {};
        tx.filter(t=> t.type === 'expense' || t.type === 'invest') // incluir investimentos para visualizar alocação
          .forEach(t=>{
              byCat[t.category] = (byCat[t.category] || 0) + Number(t.amount);
          });
        const labels = Object.keys(byCat);
        const data = labels.map(l=> byCat[l]);
        const colors = generateColors(labels.length);

        const cfg = {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data,
                    backgroundColor: colors,
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {legend:{display:false}}
            }
        };

        if (pieChart) pieChart.destroy();
        pieChart = new Chart(pieCanvas.getContext('2d'), cfg);
        renderPieLegend(labels, colors);
    }

    function renderPieLegend(labels, colors){
        const el = document.getElementById('pie-legend');
        el.innerHTML = '';
        labels.forEach((l,i)=>{
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-dot" style="background:${colors[i]}"></div><span>${l}</span>`;
            el.appendChild(item);
        });
    }

    function updateLineChart(){
        const tx = loadTransactions();
        // agrupar por mês (YYYY-MM) e tipo
        const monthsSet = new Set();
        const map = {}; // map[month] = {income:0, expense:0, invest:0}
        tx.forEach(t=>{
            const m = monthKey(t.date);
            monthsSet.add(m);
            map[m] = map[m] || {income:0, expense:0, invest:0};
            if (t.type === 'income') map[m].income += Number(t.amount);
            if (t.type === 'expense') map[m].expense += Number(t.amount);
            if (t.type === 'invest') map[m].invest += Number(t.amount);
        });
        const months = Array.from(monthsSet).sort();
        // se estiver vazio, preencher últimos 6 meses
        if (months.length === 0){
            const now = new Date();
            for (let i=5;i>=0;i--){
                const d = new Date(now.getFullYear(), now.getMonth()-i,1);
                const m = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
                months.push(m);
                map[m] = {income:0, expense:0, invest:0};
            }
        }
        const labels = months.map(m => {
            const [y,mm] = m.split('-').map(Number);
            const d = new Date(y, mm-1,1);
            return d.toLocaleString('pt-BR', {month:'short', year: '2-digit'});
        });
        const incomeData = months.map(m => (map[m]||{}).income || 0);
        const expenseData = months.map(m => (map[m]||{}).expense || 0);
        const investData = months.map(m => (map[m]||{}).invest || 0);

        const cfg = {
            type:'line',
            data:{
                labels,
                datasets:[
                    {label:'Recebido', data: incomeData, borderColor:'#2d7a6f', backgroundColor:'rgba(45,122,111,0.12)', tension:0.3, fill:true},
                    {label:'Gasto', data: expenseData, borderColor:'#e74c3c', backgroundColor:'rgba(231,76,60,0.08)', tension:0.3, fill:true},
                    {label:'Investido', data: investData, borderColor:'#f1c40f', backgroundColor:'rgba(241,196,15,0.08)', tension:0.3, fill:true}
                ]
            },
            options:{
                responsive:true,
                maintainAspectRatio:false,
                plugins:{
                    legend:{position:'bottom'}
                },
                scales:{
                    y:{beginAtZero:true, ticks:{callback: v => 'R$ ' + v}}
                }
            }
        };

        if (lineChart) lineChart.destroy();
        lineChart = new Chart(lineCanvas.getContext('2d'), cfg);
    }

    function generateColors(n){
        // paleta simples
        const palette = ['#7ec8c1', '#8b8b8b', '#f39c12', '#3498db', '#9b59b6', '#e74c3c', '#2ecc71', '#f1c40f'];
        const res = [];
        for (let i=0;i<n;i++){
            res.push(palette[i % palette.length]);
        }
        return res;
    }

    // ---------- objective UI ----------
    function loadAndRenderObjective(){
        const obj = loadObjective();
        if (obj && obj.trim() !== ''){
            objectiveDisplay.textContent = obj;
        } else {
            objectiveDisplay.textContent = 'Clique em "Editar objetivo" para definir';
        }
    }

    editObjectiveBtn.addEventListener('click', ()=>{
        objectiveInput.value = loadObjective();
        objectiveDisplay.classList.add('hidden');
        objectiveInput.classList.remove('hidden');
        objectiveInput.focus();
    });

    objectiveInput.addEventListener('keydown', (e)=>{
        if (e.key === 'Enter'){
            const v = objectiveInput.value.trim();
            saveObjective(v);
            objectiveInput.classList.add('hidden');
            objectiveDisplay.classList.remove('hidden');
            loadAndRenderObjective();
        } else if (e.key === 'Escape'){
            objectiveInput.classList.add('hidden');
            objectiveDisplay.classList.remove('hidden');
        }
    });
    objectiveInput.addEventListener('blur', ()=>{
        // salvar no blur também
        const v = objectiveInput.value.trim();
        saveObjective(v);
        objectiveInput.classList.add('hidden');
        objectiveDisplay.classList.remove('hidden');
        loadAndRenderObjective();
    });

    // ---------- goals (metas) ----------
    function openGoalModal(){
        goalModal.classList.remove('hidden');
        goalModal.setAttribute('aria-hidden','false');
        goalNameInput.value = '';
        goalTargetInput.value = '';
        goalCategoryInput.value = '';
        goalNameInput.focus();
    }
    function closeGoalModal(){
        goalModal.classList.add('hidden');
        goalModal.setAttribute('aria-hidden','true');
    }
    addGoalBtn.addEventListener('click', openGoalModal);
    cancelGoalBtn.addEventListener('click', closeGoalModal);

    saveGoalBtn.addEventListener('click', ()=>{
        const name = goalNameInput.value.trim();
        const target = parseFloat(goalTargetInput.value) || 0;
        let category = goalCategoryInput.value.trim();
        if (!name) return alert('Nome da meta é obrigatório');
        if (!category) category = `Meta:${name}`;
        const goals = loadGoals();
        goals.push({id: Date.now(), name, target, category, saved: 0});
        saveGoals(goals);
        closeGoalModal();
        renderGoals();
        // opcional: criar categoria associada automáticamente (não precisa persistir além dos tx categories)
    });

    function renderGoals(){
        const goals = loadGoals();
        goalsListEl.innerHTML = '';
        if (goals.length === 0){
            goalsListEl.innerHTML = '<div class="meta-item">Nenhuma meta ainda</div>';
            return;
        }
        goals.forEach(g=>{
            const div = document.createElement('div');
            const saved = computeSavedForGoal(g);
            const pct = g.target > 0 ? Math.min(100, Math.round((saved / g.target)*100)) : 0;
            div.className = 'goal-row';
            div.innerHTML = `<div class="goal-info">
                                <div class="goal-name">${g.name}</div>
                                <div class="goal-meta">Alvo: ${moneyFmt(Number(g.target))} • Arrecadado: ${moneyFmt(saved)} (${pct}%)</div>
                             </div>
                             <div class="goal-actions">
                                <button class="btn-small add-to-goal" data-category="${g.category}">Adicionar investimento</button>
                             </div>`;
            goalsListEl.appendChild(div);
        });

        // attach handlers to add-to-goal
        document.querySelectorAll('.add-to-goal').forEach(btn=>{
            btn.addEventListener('click', ()=>{
                const category = btn.dataset.category;
                // abrir prompt simples para adicionar um investimento e criar transação do tipo invest
                const val = parseFloat(prompt('Valor a adicionar na meta (R$):', '0')) || 0;
                if (val <= 0) return;
                const desc = `Aporte para ${category.replace(/^Meta:/,'')}`;
                addTransaction({date: (new Date()).toISOString().slice(0,10), description: desc, category, type:'invest', amount: val});
                refreshAll();
            });
        });
    }

    function computeSavedForGoal(g){
        const tx = loadTransactions();
        return tx.filter(t=> t.type === 'invest' && t.category === g.category)
                 .reduce((s,t)=> s + Number(t.amount), 0);
    }

    // ---------- transações ----------
    function addTransaction(t){
        const arr = loadTransactions();
        t.id = t.id || Date.now();
        arr.push(t);
        saveTransactions(arr);
    }

    // função pública para debug: window.addTransaction(...)
    window.addTransaction = addTransaction;

    // ---------- inicialização de charts e UI ----------
    function refreshAll(){
        renderTotals();
        renderTransactionsTable();
        updatePieChart();
        updateLineChart();
        renderGoals();
        loadAndRenderObjective();
    }

    // Inicializar
    document.addEventListener('DOMContentLoaded', ()=>{
        // inicial render
        refreshAll();
    });

    // fechar modal clicando fora do conteúdo
    goalModal.addEventListener('click', (e)=>{
        if (e.target === goalModal) closeGoalModal();
    });

    // Expõe algumas funções para facilitar testes
    window.numus = {
        refreshAll,
        loadTransactions,
        saveTransactions,
        loadGoals,
        saveGoals,
        loadObjective,
        saveObjective
    };

})();