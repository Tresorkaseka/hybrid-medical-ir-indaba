// Display values frozen from results/exp1_decision_eos_bge.json, 18 November 2026.
const quality = {"2021": [0.27467869122781385, 0.3033226663327053, 0.39551881718260395, 0.41331416045481306, 0.4017780902948165, 0.4152923761762291, 0.37583577875290697, 0.3928425189511914], "2022": [0.2537529806881694, 0.2774786528492197, 0.4110905137688232, 0.42278550518749325, 0.4737894482334894, 0.4790650697710868, 0.4131288995451999, 0.4203761759546633]};
const labels=['BM25','A','B','C','D','E','D′','E′'];
document.querySelector('#quality-chart').innerHTML=Object.entries(quality).map(([year,values])=>`<div class="quality-year fragment" data-fragment-index="${year==='2021'?0:1}"><h3>${year}</h3>${values.map((v,i)=>`<div class="bar-row ${i===5?'final':''}"><p>${labels[i]}</p><div class="bar-track"><div class="bar" style="width:${v/.5*100}%"></div></div><p class="bar-value">${v.toFixed(3).replace('.',',')}</p></div>`).join('')}</div>`).join('');
Reveal.initialize({width:1280,height:720,margin:0,controls:true,progress:true,slideNumber:'c/t',hash:true,center:false,fragments:true,fragmentInURL:false,transition:matchMedia('(prefers-reduced-motion: reduce)').matches?'none':'slide',transitionSpeed:'default',pdfSeparateFragments:false,plugins:[RevealNotes]});

// Follow a preference change without requiring a page reload.
const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
motionPreference.addEventListener('change', event => {
  Reveal.configure({ transition: event.matches ? 'none' : 'slide' });
});
