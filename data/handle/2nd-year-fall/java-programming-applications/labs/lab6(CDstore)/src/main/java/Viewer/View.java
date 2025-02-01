package Viewer;

import java.util.Scanner;

import Bean.Disk;
import Bean.User;

public class View {
	
	private Scanner inScanner=new Scanner(System.in);

	public void welcome() {
		System.out.println("Welcome CDStore! Enter h for Help!");
		
	}

	public String getMessage() {
		String tmpString=inScanner.next();
		
		return tmpString;
	}

	public User addUser() {
	
		User user=new User();
		System.out.println("ADDING USERS");
		System.out.println("Enter User's Name:");
		user.setName(getMessage());
		System.out.println("Enter User's Id:");
		user.setId(inScanner.nextInt());
		System.out.println("Enter User's Money:");
		user.setMoney(inScanner.nextDouble());
		
		return user;
	}

	public User delUser() {
		
		User user=new User();
		System.out.println("DELETE USERS");
		System.out.println("Enter User's Name:");
		user.setName(getMessage());
		System.out.println("Enter User's Id:");
		user.setId(inScanner.nextInt());
		
		return user;
	}

	public Disk addDisk() {
		Disk newDisk= new Disk();
		System.out.println("ADDING DISKS");
		System.out.println("Enter Disk's Name:");
		newDisk.setName(getMessage());
		System.out.println("Enter Disk's Quantity:");
		newDisk.setNum(inScanner.nextInt());
		System.out.println("Enter Disk's Money:");
		newDisk.setMoney(inScanner.nextDouble());
		
		return newDisk;
	}

	public User rent() {
		User user=new User();
		System.out.println("RENT");
		System.out.println("Enter User's Name:");
		user.setName(getMessage());
		System.out.println("Enter User's Id:");
		user.setId(inScanner.nextInt());
		Disk disk=new Disk();
		System.out.println("Enter the Disk to Rent:");
		disk.setName(getMessage());
		System.out.println("Enter the Number of Disks:");
		disk.setNum(inScanner.nextInt());
		user.getBorrowed().add(disk);
		
		return user;
	}

	public User buy() {
		User user=new User();
		System.out.println("BUY");
		System.out.println("Enter User's Name:");
		user.setName(getMessage());
		System.out.println("Enter User's Id:");
		user.setId(inScanner.nextInt());
		Disk disk=new Disk();
		System.out.println("Enter the Disk to Buy:");
		disk.setName(getMessage());
		System.out.println("Enter the Number of Disks:");
		disk.setNum(inScanner.nextInt());
		user.getBorrowed().add(disk);
		
		return user;
	}
	
}
