setTimeout(function () {
    element = document.getElementById('splashscreenbild_text')
    element.remove()
    element = document.getElementById('splashscreenbild')
    element.remove()
    element = document.getElementById('splashscreen')
    element.remove()
  }, 2000)

document.getElementById('start').value = new Date().toISOString().slice(0, 10);


document.addEventListener('input', (evt) => {
    console.log('run');
    if (document.getElementById('passwort').value == "" || document.getElementById('benutzername123').value == "" || document.getElementById('prüfung').value == ""){
        zweiterknopf.disabled = true;
    }
    else {
        zweiterknopf.disabled = false;
    }
  });


eel.expose(abruf_wiki_daten);
async function abruf_wiki_daten(){
    var selectElement = document.getElementById('prüfung');
    selectElement.length = 0;
    document.getElementById('platzhalter1').id = 'loader';
    zweiterknopf.disabled = true;
    var datum = document.getElementById("start").value;
    const wiki_daten_liste=await eel.wiki_seiten_abrufen(datum)()

    console.log(wiki_daten_liste)

    wiki_daten_liste.forEach(function (item, index) {
        selectElement.options[selectElement.options.length]= new Option(item)
      });
    
    document.getElementById('loader').id = 'platzhalter1';
    if (wiki_daten_liste.length==0) {
    alert("Es liegen keine versäumten Rückmeldungen vor.")
    };
    
    
    }

eel.expose(abfrage);
async function abfrage(){
    var bestätigung=confirm("Sollen die Erinnerungen wirklich versendet werden?")
    var log=false
    if (bestätigung){
        zweiterknopf.disabled = true;
        document.getElementById('platzhalter').id = 'loader';
        var benutzername = document.getElementById("benutzername123").value;
        var passwort = document.getElementById("passwort").value;

        const selected = document.querySelectorAll('#prüfung option:checked');
        const values = Array.from(selected).map(el => el.value);
        const iterator = values.values();

        var log = await eel.check_lehrenden_mail(values)();

        if (log != "korrekt"){
            document.getElementById('loader').id = 'platzhalter';
            alert("Es fehlen für mindestens eine Prüfung E-Mail-Adressen");
            return
        }
        var log=await eel.check_mail_credentials(benutzername, passwort)();
        console.log(log)
        if (log === "korrekt"){
            
            var tage = document.getElementById("tage").value;
            var benutzername = document.getElementById("benutzername123").value;
            var passwort = document.getElementById("passwort").value;
    
            for (const value of iterator) {
                const ergebnis=await eel.rm_mails_senden(value,tage,benutzername,passwort)()
                var table = document.getElementById("table");
                var row = table.insertRow(-1);
                var cell1 = row.insertCell(0);
                var cell2 = row.insertCell(1);
                var cell3 = row.insertCell(2);
                var cell4 = row.insertCell(3);
                cell1.innerHTML = ergebnis[0];
                cell2.innerHTML = ergebnis[1];
                cell3.innerHTML = ergebnis[2];
                cell4.innerHTML = ergebnis[3];
                  }
            document.getElementById('loader').id = 'platzhalter';
              
            var datum = document.getElementById("start").value;
            const wiki_daten_liste=await eel.wiki_seiten_abrufen(datum)()
            
            var selectElement = document.getElementById('prüfung');
            document.getElementById("prüfung").innerHTML = "";
            wiki_daten_liste.forEach(function (item, index) {
                selectElement.options[selectElement.options.length]= new Option(item)
            })}
        
        else{
            document.getElementById('loader').id = 'platzhalter';
            alert("Falsche Logindaten")};
    }
    else{
        alert("Aktion wurde abgebrochen");
    
    }

}


