import {Outlet} from "react-router";
import Footer from "../pages/HomeLayout/Footer.tsx";
import Navbar from "../pages/HomeLayout/Navbar.tsx";


function HomeLayout() {
    return (
        <div className="flex flex-col h-screen">
            <Navbar/>
            <main className="flex-1 flex flex-col">
                <Outlet/>
            </main>
            <Footer/>
        </div>
    );
}

export default HomeLayout;