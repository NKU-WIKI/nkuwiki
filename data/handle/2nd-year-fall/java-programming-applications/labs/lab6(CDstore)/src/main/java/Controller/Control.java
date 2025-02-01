package Controller;

import java.util.Scanner;
import Viewer.View;

public class Control {
	private Mapper.Map st;
	private View vwView;
	private Scanner cScanner=new Scanner(System.in);
	
	public Control() {
		st=new Mapper.Map();
		vwView=new View();
	}
	
	private void starthere() {
		vwView.welcome();
		while(parser(vwView.getMessage()));
	}
	
	public static void main(String[] args) {
		Control boss=new Control();
		boss.starthere();
	}
	
	private void addUser() {
		while (true) {
			
			st.addUser(vwView.addUser());
			System.out.println("Finish");
			System.out.println("Do you wanna add again?[y/n]");
			
			if(cScanner.next().equals("n")) {
				break;
			}
		}

	}
	private void delUser() {
		while (true) {
			
			st.delUser(vwView.delUser());
			System.out.println("Finish");
			System.out.println("Do you wanna add again?[y/n]");
			
			if(cScanner.next().equals("n")) {
				break;
			}
		}
	}
	
	private void addCD() {
		while (true) {
			
			st.addDisk(vwView.addDisk());
			System.out.println("Finish");
			System.out.println("Do you wanna add again?[y/n]");
			
			if(cScanner.next().equals("n")) {
				break;
			}
		}	
	}
	
	private void reportStore() {
		st.reportStore();
		
	}
	private void reportUser() {
		st.reportUser();
		
	}
	
	private void rentCD() {
		while (true) {
			
			st.rent(vwView.rent());
			System.out.println("Finish");
			System.out.println("Do you wanna add again?[y/n]");
			
			if(cScanner.next().equals("n")) {
				break;
			}
		}	
		
	}
	
	private void buyCD() {
		while (true) {
			
			st.buy(vwView.buy());
			System.out.println("Finish");
			System.out.println("Do you wanna add again?[y/n]");
			
			if(cScanner.next().equals("n")) {
				break;
			}
		}	
	}


	private boolean parser(String s) {
		switch (s) {
		case "h":
		case "help":
			help();
			break;
		case "b":
		case "buy":
			buyCD();
			break;
		case "r":
		case "rent":
			rentCD();
			break;
		case "ru":
		case "reportUser":
			reportUser();
			break;
		case "rd":
		case "reportDisk":
			reportStore();
			break;
		case "ac":
		case "addCD":
			addCD();
			break;
		case "au":
		case "addUser":
			addUser();
			break;
		case "du":
		case "deleteUser":
			delUser();
			break;
		case "exit":
			return false;
		default:
			System.out.println("Unknown Command");
			break;
		}
		return true;
	}

	private void help() {
		System.out.println("This is Help: ");
		System.out.println("Commands: "
				+ "buy disks:buy/b "
				+ "rent disks:rent/r "
				+ "add user:addUser/au ");
		System.out.println( "add disk:addCD/ac "
				+ "delete user:deleteUser/du "
				+ "check all users:reportUser/ru "
				+ "check all disks:reportDisk/rd "
				+ "exit:exit");
		
	}

	
}
