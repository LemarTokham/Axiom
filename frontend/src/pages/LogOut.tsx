import {useAuthToken} from "@/hooks/use-auth-token.ts";
import {Navigate} from "react-router"


function LogOut() {

    const {removeAuthToken} = useAuthToken()
    removeAuthToken()

    return (
        <Navigate replace={true} to="/"/>
    );
}

export default LogOut;