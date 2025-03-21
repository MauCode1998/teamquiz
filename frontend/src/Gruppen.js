import React from "react";
import { Link } from "react-router-dom";



function Gruppen() {
    const alleGruppen = ["Quizzers","Rizzers"];
    const listItems = alleGruppen.map(einzelGruppe => 
        <li key={einzelGruppe}>
                <Link to= {`/gruppe?name=${encodeURIComponent(einzelGruppe)}`}>{einzelGruppe}</Link>
        </li>
    )

    return (
        <div className='mittelPage'>
            <h1>Meine Gruppen</h1>
            <ul>{listItems}</ul>
        </div>
    );
}



export default Gruppen