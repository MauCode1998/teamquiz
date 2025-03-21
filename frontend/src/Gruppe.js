import React from "react";
import { Link, useSearchParams } from "react-router-dom";


function Gruppe() {
    const alleFächer = ["OOP","Info","Minfo"];
    const [searchparams] = useSearchParams();
    const gruppenName = searchparams.get("name")
    const listItems = alleFächer.map(einzelFach => 
        <li key={einzelFach}>
                <Link to= {`/fach?name=${encodeURIComponent(einzelFach)}&gruppenid=${encodeURIComponent("1")}`}>{einzelFach}</Link>
        </li>
    )

    return (
        <div className='mittelPage'>
            <h1>Fächer von {gruppenName}</h1>
            <ul>{listItems}</ul>
        </div>
    );
}



export default Gruppe