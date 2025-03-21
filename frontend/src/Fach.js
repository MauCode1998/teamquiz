import React from "react";
import { useSearchParams,Link } from "react-router-dom";



function Fach() {
    const [parameter] = useSearchParams();
    const fachname = parameter.get("name");
    const gruppenId = parameter.get("gruppenid")
    const alleKarteikarten = ["Was ist der coolste Boi?","Wie groß war Napoleon?","Ist Steak groß?"]
    const kartenId = "1"

    const kartenHTML = alleKarteikarten.map(karteikarte =>
        <li key = {karteikarte}>
            <Link to= {`/karte?kartenid=${encodeURI(kartenId)}`}>{karteikarte}</Link>
        </li>
    )

    return (
        <div className='mittelPage'>

            <h1 className = 'mainPageUeberschrift'>{fachname} von Gruppe {gruppenId}</h1>
            <br>
            </br>
            <h2>Alle Karteikarten:</h2>
            <ol>{kartenHTML}</ol>

        </div>
    );
}



export default Fach