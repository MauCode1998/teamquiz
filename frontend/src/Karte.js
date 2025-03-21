import React from 'react';
import { useSearchParams } from 'react-router-dom';

function Karte() {
    const [paramater] = useSearchParams();
    const kartenid = paramater.get("kartenid")
    const kartendata = [{"Frage":"Was ist der Sinn des Lebens?","FalscheAntwort1":"Essen","FalscheAntwort2":"sdsdd","FalscheAntwort3":"sdsd","RichtigeAntwort":"Chillen"}]
    return (
        <div className='mittelPage'>
            <h1> Hier stehen die Karteninfos</h1>
            <h2>Frage: {kartendata[0]["Frage"]}</h2>
            <h3>Falsche Antwort 1: {kartendata[0]["FalscheAntwort1"]}</h3>
            <h3>Falsche Antwort 2: {kartendata[0]["FalscheAntwort2"]}</h3>
            <h3>Falsche Antwort 3: {kartendata[0]["FalscheAntwort3"]}</h3>
            <h3>Falsche Antwort 4: {kartendata[0]["RichtigeAntwort"]}</h3>
        </div>
    );
}


export default Karte