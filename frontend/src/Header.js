import React from 'react'

function Header() {
    const listenpunkt1 = "Startseite";
    const listenpunkt2 = "Login";
    
    return(
        <header >
            <h1 className = 'pageheader'>Team Quiz</h1>
            <div className = 'headerNavigation'>
                <a className = 'headerNavigationItem' href="/">Startseite</a>
                <a className = 'headerNavigationItem' href="/login">Login</a>
            </div>
            
        </header>
    );
}


export default Header